import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from controllers.db_controller import get_session_local
from common.services.session_service import SessionService
from controllers.sheets_controller import get_financials, test_sheets_connection, reset_offline_mode
from models.coach_model import Coach
from models.player_model import Player
from models.user_model import User
from models.session_model import Session, SessionStatus
# Importar las funciones de sincronización
from controllers.calendar_controller import sync_db_to_calendar, sync_single_session

# Conexión a BD
SessionLocal = get_session_local()

def show():
    st.title("Administración")
    user_type = st.session_state['user_type']

    if user_type == 'admin':
        st.subheader("📊 Dashboard General")

        with SessionLocal() as db:
            total_players = db.query(Player).count()
            total_coaches = db.query(Coach).count()
            now = datetime.now()
            start_of_month = now.replace(day=1)
            start_of_week = now - timedelta(days=now.weekday())

            sessions_month = db.query(Session).filter(Session.start_time >= start_of_month).count()
            sessions_week = db.query(Session).filter(Session.start_time >= start_of_week).count()

        # Obtenemos datos financieros 
        df_financial = get_financials()

        ingresos_mensuales = df_financial['Ingresos'].sum() if 'Ingresos' in df_financial.columns else 0
        gastos_mensuales = df_financial['Gastos'].sum() if 'Gastos' in df_financial.columns else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏃‍♂️ Jugadores", f"{total_players}")
            st.metric("🎯 Coaches", f"{total_coaches}")
        with col2:
            st.metric("📅 Sesiones Mes", f"{sessions_month}")
            st.metric("📆 Sesiones Semana", f"{sessions_week}")
        with col3:
            st.metric("📈 Ingresos (€)", f"{ingresos_mensuales:,.2f} €")
            st.metric("📉 Gastos (€)", f"{gastos_mensuales:,.2f} €")

    # Pestañas para navegar entre las secciones
    tabs = []
    if user_type == 'admin':
        tabs = ["Ver sesiones/CRUD sesiones", "Sincronización Calendar", "Informe Financiero", "Usuarios", "Diagnóstico"]
    elif user_type == 'coach':
        tabs = ["Mis sesiones"]

    selected_tab = st.selectbox("Selecciona una opción:", tabs)

    with SessionLocal() as db:

        if selected_tab == "Ver sesiones/CRUD sesiones" and user_type == 'admin':
            st.subheader("Gestión de Sesiones (Admin)")
            
            # Mostrar todas las sesiones en formato tabla
            st.write("### Lista de Sesiones")
            all_sessions = db.query(Session).all()
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                filter_sync = st.selectbox("Filtrar por estado de sincronización:", 
                                          ["Todas", "Sincronizadas", "No sincronizadas"])
            with col2:
                filter_status = st.selectbox("Filtrar por estado de sesión:", 
                                            ["Todas"] + [status.value for status in SessionStatus])
            
            # Aplicar filtros
            filtered_sessions = all_sessions
            if filter_sync == "Sincronizadas":
                filtered_sessions = [s for s in filtered_sessions if s.calendar_event_id]
            elif filter_sync == "No sincronizadas":
                filtered_sessions = [s for s in filtered_sessions if not s.calendar_event_id]
                
            if filter_status != "Todas":
                filtered_sessions = [s for s in filtered_sessions if s.status.value == filter_status]
            
            # Generar datos para la tabla
            session_data = []
            for s in filtered_sessions:
                # Obtener información del coach y jugador
                coach = db.query(Coach).filter_by(coach_id=s.coach_id).first()
                player = db.query(Player).filter_by(player_id=s.player_id).first()
                
                coach_name = "Desconocido"
                player_name = "Desconocido"
                
                if coach:
                    coach_user = db.query(User).filter_by(user_id=coach.user_id).first()
                    if coach_user and coach_user.name:
                        coach_name = coach_user.name
                
                if player:
                    player_user = db.query(User).filter_by(user_id=player.user_id).first()
                    if player_user and player_user.name:
                        player_name = player_user.name
                
                # Determinar el símbolo de sincronización
                sync_status = "✅" if s.calendar_event_id else "❌"
                
                # Formato de fecha y hora
                fecha = s.start_time.strftime('%d/%m/%Y')
                hora_inicio = s.start_time.strftime('%H:%M')
                hora_fin = s.end_time.strftime('%H:%M')
                
                # Agregar los datos
                session_data.append({
                    "ID": s.id,
                    "🔄": sync_status,
                    "Fecha": fecha,
                    "Hora": f"{hora_inicio} - {hora_fin}",
                    "Jugador": player_name,
                    "Entrenador": coach_name,
                    "Estado": s.status.value,
                })
            
            # Crear el DataFrame
            if session_data:
                df_sessions = pd.DataFrame(session_data)
                st.dataframe(df_sessions, use_container_width=True)
                
                # Sección para acciones de sesión
                st.write("### Acciones")
                
                # Permitir al usuario seleccionar una sesión para realizar acciones
                session_ids = [s["ID"] for s in session_data]
                selected_session_id = st.selectbox("Selecciona una sesión:", session_ids)
                
                # Obtener la sesión seleccionada
                selected_session = db.query(Session).filter(Session.id == selected_session_id).first()
                
                if selected_session:
                    # Crear botones para acciones
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if st.button("✅ Completar"):
                            SessionService.update(db, selected_session_id, status=SessionStatus.COMPLETED)
                            st.success(f"Sesión {selected_session_id} marcada como completada")
                            st.rerun()
                    with col2:
                        if st.button("📝 Modificar"):
                            # Esta acción abriría un formulario para modificar
                            st.session_state["editing_session"] = selected_session_id
                    with col3:
                        if st.button("⏸️ Cancelar"):
                            SessionService.update(db, selected_session_id, status=SessionStatus.CANCELED)
                            st.success(f"Sesión {selected_session_id} cancelada")
                            st.rerun()
                    with col4:
                        if st.button("🗑️ Eliminar"):
                            if SessionService.delete(db, selected_session_id):
                                st.success(f"Sesión {selected_session_id} eliminada")
                                st.rerun()
                            else:
                                st.error(f"Error al eliminar la sesión {selected_session_id}")
                    
                    # Si estamos en modo edición, mostrar formulario
                    if "editing_session" in st.session_state and st.session_state["editing_session"] == selected_session_id:
                        st.write("### Editar Sesión")
                        
                        # Obtener información actual
                        current_start = selected_session.start_time
                        current_end = selected_session.end_time
                        current_notes = selected_session.notes or ""
                        
                        # Formulario de edición
                        edit_date = st.date_input("Fecha", current_start.date())
                        col1, col2 = st.columns(2)
                        with col1:
                            edit_start_time = st.time_input("Hora inicio", current_start.time())
                        with col2:
                            edit_end_time = st.time_input("Hora fin", current_end.time())
                        
                        edit_notes = st.text_area("Notas", current_notes)
                        
                        if st.button("Guardar cambios"):
                            # Combinar fecha y hora
                            new_start = datetime.combine(edit_date, edit_start_time)
                            new_end = datetime.combine(edit_date, edit_end_time)
                            
                            # Actualizar la sesión
                            SessionService.update(
                                db, 
                                selected_session_id, 
                                start_time=new_start,
                                end_time=new_end,
                                notes=edit_notes
                            )
                            
                            # Limpiar estado de edición y recargar
                            st.session_state.pop("editing_session", None)
                            st.success("Sesión actualizada correctamente")
                            st.rerun()
                        
                        if st.button("Cancelar edición"):
                            st.session_state.pop("editing_session", None)
                            st.rerun()
            else:
                st.info("No hay sesiones que coincidan con los filtros seleccionados.")
                        
        elif selected_tab == "Sincronización Calendar" and user_type == 'admin':
            st.subheader("Sincronización con Google Calendar")
            
            # Mostrar advertencia sobre el modo offline
            st.warning("""
            **Modo de Sincronización Manual**
            
            Debido a las limitaciones de tasa de la API de Google Calendar, se ha implementado un modo de sincronización manual controlada:
            
            1. Las sesiones se crean y actualizan primero en la base de datos local
            2. La sincronización con Google Calendar se realiza de forma manual y controlada
            3. Las sesiones se sincronizan de una en una para evitar errores de límite de tasa
            
            Esta estrategia evita los errores de "Rate Limit Exceeded".
            """)
            
            # Contador de sesiones pendientes
            pending_sessions = db.query(Session).filter(Session.calendar_event_id.is_(None)).all()
            pending_count = len(pending_sessions)
            
            # Estadísticas de sincronización
            total_sessions = db.query(Session).count()
            synced_sessions = db.query(Session).filter(Session.calendar_event_id.isnot(None)).count()
            
            st.write("### Estadísticas de Sincronización")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de sesiones", f"{total_sessions}")
            with col2:
                st.metric("Sesiones sincronizadas", f"{synced_sessions}")
            with col3:
                sync_percent = (synced_sessions / total_sessions * 100) if total_sessions > 0 else 0
                st.metric("Porcentaje sincronizado", f"{sync_percent:.1f}%")
            
            # Sección de sincronización controlada
            st.write("### Sincronización Manual")
            
            if pending_count == 0:
                st.success("¡Todas las sesiones están sincronizadas con Google Calendar!")
            else:
                st.info(f"Hay {pending_count} sesiones pendientes de sincronizar con Google Calendar")
                
                # Mostrar la primera sesión pendiente
                if pending_sessions:
                    session = pending_sessions[0]
                    
                    st.write("#### Próxima sesión a sincronizar:")
                    
                    # Obtener información adicional
                    coach = db.query(Coach).filter_by(coach_id=session.coach_id).first()
                    player = db.query(Player).filter_by(player_id=session.player_id).first()
                    
                    coach_name = "Desconocido"
                    player_name = "Desconocido"
                    
                    if coach:
                        coach_user = db.query(User).filter_by(user_id=coach.user_id).first()
                        if coach_user and coach_user.name:
                            coach_name = coach_user.name
                        
                    if player:
                        player_user = db.query(User).filter_by(user_id=player.user_id).first()
                        if player_user and player_user.name:
                            player_name = player_user.name
                    
                    st.write(f"ID: {session.id}")
                    st.write(f"Coach: {coach_name} (ID: {session.coach_id})")
                    st.write(f"Jugador: {player_name} (ID: {session.player_id})")
                    st.write(f"Fecha: {session.start_time.strftime('%d/%m/%Y')} - Hora: {session.start_time.strftime('%H:%M')} a {session.end_time.strftime('%H:%M')}")
                    st.write(f"Estado: {session.status.value}")
                    
                    if st.button("Sincronizar Esta Sesión con Google Calendar"):
                        with st.spinner("Sincronizando sesión con Google Calendar..."):
                            try:
                                result = sync_single_session(db, session.id)
                                if result:
                                    st.success(f"¡Sesión {session.id} sincronizada correctamente!")
                                else:
                                    st.error(f"Error al sincronizar la sesión {session.id}")
                            except Exception as e:
                                st.error(f"Error durante la sincronización: {str(e)}")
                                
                        st.rerun()

        elif selected_tab == "Mis sesiones" and user_type == 'coach':
            st.subheader("Mis Sesiones (Coach)")
            coach = db.query(Coach).filter_by(user_id=st.session_state['user_id']).first()
            if coach:
                # Obtener todas las sesiones del coach
                sess_list = db.query(Session).filter_by(coach_id=coach.coach_id).all()
                
                # Crear datos para la tabla
                session_data = []
                for s in sess_list:
                    # Obtener información del jugador
                    player = db.query(Player).filter_by(player_id=s.player_id).first()
                    player_name = "Desconocido"
                    
                    if player:
                        player_user = db.query(User).filter_by(user_id=player.user_id).first()
                        if player_user and player_user.name:
                            player_name = player_user.name
                    
                    # Determinar el símbolo de sincronización
                    sync_status = "✅" if s.calendar_event_id else "❌"
                    
                    # Formato de fecha y hora
                    fecha = s.start_time.strftime('%d/%m/%Y')
                    hora_inicio = s.start_time.strftime('%H:%M')
                    hora_fin = s.end_time.strftime('%H:%M')
                    
                    # Agregar los datos
                    session_data.append({
                        "ID": s.id,
                        "🔄": sync_status,
                        "Fecha": fecha,
                        "Hora": f"{hora_inicio} - {hora_fin}",
                        "Jugador": player_name,
                        "Estado": s.status.value
                    })
                
                # Crear el DataFrame
                if session_data:
                    df_sessions = pd.DataFrame(session_data)
                    st.dataframe(df_sessions, use_container_width=True)
                    
                    # Acciones para sesiones
                    st.write("### Acciones")
                    
                    # Permitir al usuario seleccionar una sesión para realizar acciones
                    session_ids = [s["ID"] for s in session_data]
                    selected_session_id = st.selectbox("Selecciona una sesión:", session_ids)
                    
                    # Crear botones para acciones
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✅ Completar"):
                            SessionService.update(db, selected_session_id, status=SessionStatus.COMPLETED)
                            st.success(f"Sesión {selected_session_id} marcada como completada")
                            st.rerun()
                    with col2:
                        if st.button("⏸️ Cancelar"):
                            SessionService.update(db, selected_session_id, status=SessionStatus.CANCELED)
                            st.success(f"Sesión {selected_session_id} cancelada")
                            st.rerun()
                    with col3:
                        if st.button("🗑️ Eliminar"):
                            if SessionService.delete(db, selected_session_id):
                                st.success(f"Sesión {selected_session_id} eliminada")
                                st.rerun()
                            else:
                                st.error(f"Error al eliminar la sesión {selected_session_id}")
                else:
                    st.info("No tienes sesiones programadas.")
            else:
                st.error("Perfil de coach no encontrado.")

        elif selected_tab == "Informe Financiero" and user_type == 'admin':
            st.subheader("Informe Financiero")
            
            # Obtener los datos financieros (ahora con respaldo en caso de error)
            df = get_financials()
            
            # Verificar si estamos usando datos de respaldo
            if 'Mes' in df.columns and len(df) == 12 and df['Mes'][0] == 'Enero':
                st.warning("""
                **Datos financieros de respaldo**
                
                Se están mostrando datos financieros simulados debido a un problema de conexión con Google Sheets.
                Consulta la pestaña de "Diagnóstico" para más información.
                """)
            
            # Mostrar los datos
            st.dataframe(df)
            
            # Mostrar gráfico de ingresos vs gastos
            if 'Ingresos' in df.columns and 'Gastos' in df.columns:
                st.write("### Ingresos vs Gastos")
                chart_data = df[['Mes', 'Ingresos', 'Gastos']].set_index('Mes') if 'Mes' in df.columns else df[['Ingresos', 'Gastos']]
                st.line_chart(chart_data)

        elif selected_tab == "Usuarios" and user_type == 'admin':
            st.subheader("Gestión de Usuarios")
            users = db.query(User).all()
            if users:
                user_data = []
                for user in users:
                    user_data.append({
                        "ID": user.user_id,
                        "Username": user.username,
                        "Nombre": user.name,
                        "Email": user.email,
                        "Teléfono": user.phone,
                        "Fecha Nacimiento": user.date_of_birth,
                        "Tipo Usuario": user.user_type.value,
                        "Nivel Permiso": user.permit_level
                    })
                df_users = pd.DataFrame(user_data)
                st.dataframe(df_users, use_container_width=True)
            else:
                st.write("No hay usuarios registrados.")
                
        elif selected_tab == "Diagnóstico" and user_type == 'admin':
            st.subheader("Diagnóstico del Sistema")
            
            st.write("### Conexión a Google Sheets")
            
            # Implementar un botón para probar la conexión
            if st.button("Probar conexión a Google Sheets"):
                with st.spinner("Probando conexión..."):
                    result = test_sheets_connection()
                
                if result["success"]:
                    st.success(result["message"])
                    if result["details"]:
                        st.write(f"**Título de la hoja:** {result['details']['sheet_title']}")
                        st.write(f"**URL de la hoja:** {result['details']['sheet_url']}")
                else:
                    st.error(result["message"])
                    if result["details"]:
                        st.write(f"**Tipo de error:** {result['details']['error_type']}")
                        st.write(f"**Mensaje de error:** {result['details']['error_message']}")
            
            # Opción para resetear el modo offline
            if st.button("Resetear modo offline para Google Sheets"):
                reset_offline_mode()
                st.success("Modo offline reseteado. En el próximo acceso se intentará conectar a Google Sheets.")
                
            st.write("### Variables de Entorno")
            from config import DATABASE_URL, SERVICE_ACCOUNT, GOOGLE_CALENDAR_ID, GOOGLE_SHEET_ID
            
            env_vars = {
                "GOOGLE_SERVICE_ACCOUNT_JSON": SERVICE_ACCOUNT,
                "GOOGLE_SHEET_ID": GOOGLE_SHEET_ID,
                "GOOGLE_CALENDAR_ID": GOOGLE_CALENDAR_ID,
                "DATABASE_URL": DATABASE_URL
            }
            
            for var, value in env_vars.items():
                file_exists = False
                if var == "GOOGLE_SERVICE_ACCOUNT_JSON" and value:
                    file_exists = os.path.exists(value)
                    st.write(f"**{var}:** {value} {'✅ (archivo existe)' if file_exists else '❌ (archivo no existe)'}")
                else:
                    st.write(f"**{var}:** {value}")
                    
            # Información sobre base de datos
            st.write("### Base de Datos")
            try:
                with SessionLocal() as db:
                    db_stats = {
                        "Usuarios": db.query(User).count(),
                        "Coaches": db.query(Coach).count(),
                        "Jugadores": db.query(Player).count(),
                        "Sesiones": db.query(Session).count(),
                        "Sesiones sincronizadas con Calendar": db.query(Session).filter(Session.calendar_event_id.isnot(None)).count()
                    }
                    
                    for stat, value in db_stats.items():
                        st.write(f"**{stat}:** {value}")
            except Exception as e:
                st.error(f"Error al conectar con la base de datos: {str(e)}")