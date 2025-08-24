# Nexaris Finances Backend

Sistema de gestión financiera personal desarrollado en Python con FastAPI y PostgreSQL.

## 📋 Requisitos Previos

-   Python 3.11 o superior
-   Git
-   PostgreSQL 14 o superior
-   pip (gestor de paquetes de Python)

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone git@github.com:tuusuario/nexaris-finances-back.git
cd nexaris-finances-back
```

### 2. Crear entorno virtual

```bash
python -m venv .venv
```

### 3. Activar entorno virtual

```bash
# En Linux/Mac:
source .venv/bin/activate

# En Windows (PowerShell):
.venv\Scripts\Activate.ps1

# En Windows (Command Prompt):
.venv\Scripts\activate.bat
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 🗄️ Configuración de Base de Datos

### Requisitos de Base de Datos

**IMPORTANTE**: Este proyecto requiere:

-   Una base de datos PostgreSQL llamada `nexaris_finances`
-   Un schema llamado `sys`

### Opción 1: Usar la configuración por defecto

Si desea usar los nombres por defecto, asegúrese de crear:

```sql
-- Crear la base de datos
CREATE DATABASE nexaris_finances;

-- Conectarse a la base de datos
\c nexaris_finances

-- Crear el schema
CREATE SCHEMA sys;
```

### Opción 2: Usar nombres personalizados

Si desea usar nombres diferentes, modifique el archivo `.env` con sus preferencias.

## ⚙️ Configuración del Archivo .env

Cree un archivo `.env` en la raíz del proyecto con la siguiente estructura:

```bash
# Configuración de PostgreSQL
PG_HOST=localhost
PG_DATABASE=nexaris_finances
PG_USER=tu_usuario
PG_PASSWORD=tu_contraseña
PG_SSLMODE=require
PG_CHANNELBINDING=require
PG_PORT=5432
PG_SCHEMA=sys
```

### Variables de Entorno Explicadas

| Variable            | Descripción                | Valor por Defecto  | Requerido |
| ------------------- | -------------------------- | ------------------ | --------- |
| `PG_HOST`           | Host de PostgreSQL         | -                  | ✅        |
| `PG_DATABASE`       | Nombre de la base de datos | `nexaris_finances` | ✅        |
| `PG_USER`           | Usuario de PostgreSQL      | -                  | ✅        |
| `PG_PASSWORD`       | Contraseña del usuario     | -                  | ✅        |
| `PG_SSLMODE`        | Modo SSL                   | `require`          | ❌        |
| `PG_CHANNELBINDING` | Binding de canal           | `require`          | ❌        |
| `PG_PORT`           | Puerto de PostgreSQL       | `5432`             | ❌        |
| `PG_SCHEMA`         | Schema de la base de datos | `sys`              | ✅        |

## 🗃️ Script de Generación de la Base de Datos

Ejecute los siguientes comandos SQL en su base de datos PostgreSQL para crear las tablas necesarias:

```sql
-- Asegúrese de estar conectado a la base de datos correcta
-- y que el schema 'sys' esté creado

-- 1) Tabla de Usuarios
CREATE TABLE sys.users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  display_name TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_active boolean DEFAULT TRUE
);

-- 2) Tipos de Cuenta
CREATE TYPE sys.account_kind AS ENUM ('asset','liability','income','expense','equity');

-- 3) Tabla de Cuentas Contables
CREATE TABLE sys.ledger_account (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES sys.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  kind sys.account_kind NOT NULL,
  last4 CHAR(4),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);

-- 4) Tabla de Asientos Contables
CREATE TABLE sys.journal_entry (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES sys.users(id) ON DELETE CASCADE,
  occurred_at TIMESTAMPTZ NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);

-- 5) Tabla de Líneas de Asiento (Débitos/Créditos)
CREATE TABLE sys.journal_line (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entry_id UUID NOT NULL REFERENCES sys.journal_entry(id) ON DELETE CASCADE,
  account_id UUID NOT NULL REFERENCES sys.ledger_account(id),
  amount NUMERIC(18,2) NOT NULL CHECK (amount > 0),
  side CHAR(1) NOT NULL CHECK (side IN ('D','C'))
);

-- 6) Índices para Optimización
CREATE INDEX idx_ledger_account_user_id ON sys.ledger_account (user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_journal_entry_user_occurred ON sys.journal_entry (user_id, occurred_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_journal_line_entry_id ON sys.journal_line (entry_id);
CREATE INDEX idx_journal_line_account_id ON sys.journal_line (account_id);
```

## 🏃‍♂️ Ejecutar la Aplicación

### Modo Desarrollo

```bash
fastapi dev app\main.py
```

### Modo Producción

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📚 Documentación de la API

Una vez que la aplicación esté ejecutándose, puede acceder a:

-   **Swagger UI**: http://localhost:8000/docs
-   **ReDoc**: http://localhost:8000/redoc

## 📁 Estructura del Proyecto

```
nexaris-finance-back/
├── app/
│   ├── api/
│   │   ├── routes.py
│   │   └── user/
│   │       └── user_routes.py
│   ├── core/
│   │   ├── config.py
│   │   └── db.py
│   ├── main.py
│   ├── models/
│   │   ├── base.py
│   │   ├── journal_entry.py
│   │   ├── journal_line.py
│   │   ├── ledger_account.py
│   │   └── user.py
│   └── schemas/
│       ├── response.py
│       └── user.py
├── requirements.txt
└── README.md
```
