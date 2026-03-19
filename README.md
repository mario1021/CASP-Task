# CASP-Task
Scripts desarrollados para la automatización de tareas relacionadas con la obtención de estructuras a partir de secuencias de proteínas.
Ambos se ejecutan por línea de comandos.

### Conversión de formato Sympred para I Tasser
Sympred es una herramienta capaz de predecir la estructura secundaria de una proteína con precisión. Esta información se puede incluir en I Tasser si se prefiere ante la predicción que este realiza, pero los formatos de salida y entrada de las herramientas no coinciden. El script desarrollado transforma la salida de Sympred a un formato aceptable por I Tasser.

#### Ejemplo de uso 
Basta con ejecutar en la terminal:
```bash
python3 nombre_programa input_file.txt output_file.txt
```
### Script para el uso automatizado de la API de Foldseek
FoldSeek, herramienta para descubrir estructuras relacionadas, posee una API para realizar programáticamente esta tarea. El script desarrollado nos permite obtener los resultados y descargarlos automáticamente, pudiendo esperar y reintentar si el servidor está caído.

#### Ejemplo de uso
```bash
 python3 Foldseek_API_script.py input.pdb output.xlsx --multimer
 ```

