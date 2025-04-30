import sys, pathlib
# añade la carpeta raíz (dos niveles arriba) al PYTHONPATH
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from config import SERVICE_ACCOUNT
import pathlib
print("SERVICE_ACCOUNT =", SERVICE_ACCOUNT)
print("Existe? ->", pathlib.Path(SERVICE_ACCOUNT).expanduser().resolve().exists())
