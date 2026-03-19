# Script para interactuar con la API de Foldseek
# Autores: Chen Xi Ye Xu, Estefani Alejandra Casallas Samper, Mario Díaz Acosta
# Mejoras: Reintentos automáticos, polling de estado y manejo de argumentos profesional.

import requests
import argparse
import pandas as pd
import time

# El script se ejecuta desde la línea de comandos
# Ejemplo de uso: python3 Foldseek_API_script.py input.pdb output.xlsx --multimer
# El argumento --multimer es opcional y activa el modo multímero en vez del modo monómero.

MAX_RETRIES = 5        # Intentos máximos si la conexión falla
RETRY_DELAY = 5        # Segundos entre reintentos de conexión
POLLING_INTERVAL = 10  # Segundos entre consultas de estado

def submit_foldseek_job(file_path, multimer=False):
    #Función para enviar el archivo a Foldseek y obtener un ticket ID.
    url = "https://search.foldseek.com/api/ticket"
    mode = "complex-3diaa" if multimer else "3diaa"
    
    # Definición de bases de datos según el modo
    multimer_db = ["pdb100", "bfmd"]
    monomer_db = ["afdb50", "afdb-swissprot", "afdb-proteome", "pdb100", "BFVD", "mgnify_esm30", "cath50", "gmgcl_id", "bfmd"]
    databases = multimer_db if multimer else monomer_db

    for attempt in range(MAX_RETRIES):
        try:
            with open(file_path, "rb") as f:
                files = {"q": f}
                # Construcción correcta de la data para requests (tuplas para llaves repetidas)
                data = [("mode", mode)]
                for db in databases:
                    data.append(("database[]", db))
                
                response = requests.post(url, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    ticket_id = response.json().get("id")
                    print(f"Ticket creado con éxito: {ticket_id}")
                    return ticket_id
                
                print(f"Intento {attempt+1}: El servidor respondió con error {response.status_code}")
        
        except (requests.exceptions.RequestException, IOError) as e:
            print(f"Intento {attempt+1}: Error de red o archivo: {e}")
        
        time.sleep(RETRY_DELAY)
    
    return None

def get_results_with_polling(ticket_id):
    #Función para consultar el estado del ticket y obtener resultados una vez que estén listos.
    url_status = f"https://search.foldseek.com/api/ticket/{ticket_id}"
    url_results = f"https://search.foldseek.com/api/result/{ticket_id}/0"

    print(f"Esperando a que Foldseek procese los datos...")

    while True:
        try:
            check = requests.get(url_status, timeout=20)
            if check.status_code == 200:
                status = check.json().get("status", "")
                
                if status == "COMPLETE":
                    print("¡Procesamiento completo! Descargando resultados...")
                    res = requests.get(url_results, timeout=30)
                    return res.json() if res.status_code == 200 else None
                
                elif status in ["ERROR", "FAILED"]:
                    print("Error: El servidor de Foldseek falló al procesar esta estructura.")
                    return None
                else:
                    print(f"Estado: {status}... reintentando en {POLLING_INTERVAL}s")
            else:
                print(f"Error consultando estado: {check.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"Error de conexión durante la espera: {e}")

        time.sleep(POLLING_INTERVAL)

def add_urls_to_results(processed_results):
    db_urls = {
        "pdb100": "https://www.rcsb.org/structure/",
        "afdb50": "https://alphafold.ebi.ac.uk/entry/",
        "afdb-swissprot": "https://alphafold.ebi.ac.uk/entry/",
        "afdb-proteome": "https://alphafold.ebi.ac.uk/entry/",
        "BFVD": "https://bfvd.foldseek.com/cluster/",
    }
    for db_name, complexes in processed_results.items():
        for complex_name, complex_data in complexes.items():
            for chain in complex_data["chains"]:
                target_id = chain["target_id"]
                if db_name in db_urls:
                    chain["url"] = f"{db_urls[db_name]}{target_id}"
                else:
                    chain["url"] = "URL not available"
    return processed_results

def parse_target(target_str):
    #Función para extraer el ID de la estructura y su descripción
    parts = target_str.split(" ", 1)
    file_part = parts[0]
    description = parts[1] if len(parts) > 1 else ""
    cif_index = file_part.find(".cif")
    structure_id = file_part[:cif_index] if cif_index != -1 else file_part
    return structure_id, description

def parse_chain(chain_str):
    return chain_str.split("_")[1] if "_" in chain_str else chain_str

def process_results(results):
    #Función para pasar los resultados a un formato más ordenado
    processed_results = {}
    for result in results.get("results", []):
        db_name = result.get("db")
        alignments = result.get("alignments", [])

        if db_name not in processed_results:
            processed_results[db_name] = {}

        for alignment_group in alignments:
            for alignment in alignment_group:
                complex_id = alignment.get("complexid")
                complex_name = f'complex_{complex_id}'
                complex_qtm = alignment.get("complexqtm", 0)
                chain_id = parse_chain(alignment.get("query"))
                e_value = alignment.get("eval")
                seq_id = alignment.get("seqId")
                target_id, target_description = parse_target(alignment.get("target"))

                if complex_name not in processed_results[db_name]:
                    processed_results[db_name][complex_name] = {
                        "chains": [],
                        "complex_qtm": complex_qtm,
                    }

                processed_results[db_name][complex_name]["chains"].append({
                    "chain_id": chain_id,
                    "seq_id": seq_id,
                    "e_value": e_value,
                    "target_id": target_id,
                    "target_description": target_description
                })

        # Ordenar por QTM
        processed_results[db_name] = dict(
            sorted(processed_results[db_name].items(), 
                   key=lambda x: x[1]["complex_qtm"], reverse=True)
        )
    
    return add_urls_to_results(processed_results)

def export_to_excel(processed_results, output_file):
    rows = []
    for db_name, complexes in processed_results.items():
        for complex_name, complex_data in complexes.items():
            for chain in complex_data["chains"]:
                rows.append({
                    "Database": db_name,
                    "Structure ID": complex_name.replace("complex_", ""),
                    "Complex QTM": complex_data["complex_qtm"],
                    "Target ID": chain["target_id"],
                    "Description": chain["target_description"],
                    "url": chain.get("url"),
                    "Chain": chain["chain_id"],
                    "Seq ID": chain["seq_id"],
                    "E-Value": chain["e_value"]
                })

    if not rows:
        print("No se encontraron resultados para exportar.")
        return

    df = pd.DataFrame(rows)
    df["db_priority"] = df["Database"].apply(lambda x: 0 if x == "pdb100" else 1)
    df = df.sort_values(by=["db_priority", "Database", "Complex QTM"], ascending=[True, True, False])
    df.drop(columns=["db_priority"]).to_excel(output_file, index=False)
    print(f"Archivo Excel guardado como: {output_file}")

def full_foldseek_pipeline(file_path, output_file, multimer=False):
    #Función principal para ejecutar todo el pipeline de Foldseek.
    ticket_id = submit_foldseek_job(file_path, multimer)
    if not ticket_id:
        print("Error al iniciar el trabajo.")
        return

    results = get_results_with_polling(ticket_id)
    if not results:
        print("No se pudieron obtener resultados válidos.")
        return

    processed = process_results(results)
    export_to_excel(processed, output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline automático para Foldseek API")
    parser.add_argument("input", help="Archivo PDB/CIF de entrada")
    parser.add_argument("output", help="Nombre del archivo Excel de salida")
    parser.add_argument("--multimer", action="store_true", help="Activar modo complejo (multímero)")

    args = parser.parse_args()