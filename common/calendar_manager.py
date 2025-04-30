# common/calendar_manager.py

# Redireccionar todas las llamadas a las funciones del nuevo controlador unificado
from controllers.calendar_controller import (
    create_calendar_event,
    update_calendar_event,
    delete_calendar_event
)

# Estas funciones son las que se llaman desde session_controller.py
# Solo son proxies para las funciones del nuevo controlador