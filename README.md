# 🧠 Content Marketing Project Manager - CrewAI

Aplicación de planificación de proyectos basada en **CrewAI** con agentes inteligentes que ayudan a organizar campañas de marketing de contenidos multicanal.

---

## 📌 Resumen Ejecutivo
Esta aplicación utiliza un **crew de 3 agentes de IA** que valida entradas con **Pydantic** y genera un **plan accionable**:
- Organización del equipo  
- Asignación de responsables  
- Secuenciación de tareas  
- Estimación de tiempos y costos  

Aunque el caso de uso está orientado a **marketing de contenidos (blog, email, redes)**, el enfoque es **generalizable** a cualquier tipo de proyecto.

---

## 🚀 Problema que resuelve
Un Project Manager suele gastar horas en:
- Organizar personas y recursos  
- Secuenciar tareas  
- Monitorear objetivos  

Esta app **sistematiza el proceso**, reduciendo tiempos de preparación y mejorando la calidad del plan inicial.

---

## ⚙️ Estructura del Proyecto
content_marketing_project_manager/
│── config/ # Configuración de crew y tareas
│── tools/ # Herramientas personalizadas
│── main.py # Script principal
│── crew.py # Definición del crew de agentes
│── types.py # Definición de tipos con Pydantic
│── README.md # Documentación del proyecto

---

## 🔧 Requisitos
- Python 3.10+  
- [CrewAI](https://pypi.org/project/crewai/)  
- Pydantic  
- OpenAI API key (u otro proveedor LLM)  

Instalación de dependencias:
pip install -r requirements.txt

▶️ Ejecución
Crear y configurar un archivo .env en la raíz con tu API key:

OPENAI_API_KEY=tu_api_key_aqui

Ejecutar la app:

python main.py
Ingresar objetivos, equipo y entregables.
El sistema devuelve un plan en un Notebook con asignación de responsables, tiempos y estimación de tokens/costos.

📊 Ejemplo de uso
Entrada:

{
  "objetivo": "Lanzar campaña de marketing digital",
  "equipo": ["PM", "Copywriter", "Diseñador", "Analista SEO"],
  "entregables": ["Posts de blog", "Emailing", "Ads sociales"]
}

Salida:

Plan de trabajo en Notebook
Estimación de tokens y costos
Distribución de tareas por responsable

👨‍💻 Autor
Francisco Moyano Escalera
Especialista en Data, AI y Automatización
📧 frannmmm419@gmail.com
🌐 GitHub