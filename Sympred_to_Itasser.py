#Este script tiene la finalidad de adaptar la salida Human-readable de Sympred a un formato compatible con I-TASSER. 
#Autores: Chen Xi Ye Xu, Estefani Alejandra Casallas Samper, Mario Díaz Acosta 
#Para la tarea de Bioinformática estructural del Máster de Bioinformática de la UAM, curso 2025-2026).

import sys 

#En línea de comandos se espera que se introduzca algo similar a: python3 nombre_programa input_file.txt output_file.txt

def parse_sympred(file_path):
    sequence = ""
    ss_pred = ""

    with open(file_path) as f:
        aa_lines = [] #Lista para almacenar las líneas de la secuencia de aminoácidos.
        ss_lines = [] #Lista para almacenar las líneas de la predicción de estructura secundaria.

        for line in f:
            if line.startswith("AA"): #Las líneas de la secuencia de aa.
                aa_lines.append(line[18:88].rstrip("\n")) #Eliminar el AA y los espacios delante para que no desalinee con SYMPRED y después y eliminar salto línea.

            elif line.startswith("SYMPRED"): #Las líneas con la predicción de estructura secundaria por SYMPRED.
                ss_lines.append(line[18:88].rstrip("\n")) #Eliminar el SYMPRED y los espacios de antes y después.

    sequence = "".join(aa_lines) #Unir las líneas de la secuencia de aa en una sola cadena.
    ss_raw = "".join(ss_lines) #Unir las líneas de la predicción de estructura secundaria en una sola cadena.

    for aa, ss_char in zip(sequence, ss_raw): #Iterar sobre ambas cadenas al mismo tiempo.
        if ss_char == " ":
            ss_pred += "X" #Si el carácter de la predicción de estructura secundaria es un espacio, agregar una X a la cadena de predicción de estructura secundaria.
        elif ss_char == "E":
            ss_pred += "S" #Si el carácter de la predicción de estructura secundaria es una E, agregar una S a la cadena de predicción de estructura secundaria.
        else:
            ss_pred += ss_char #Si el carácter de la predicción de estructura secundaria no es un espacio ni una E, agregarlo tal cual a la cadena de predicción de estructura secundaria.

    return sequence, ss_pred


def write_itasser_format(sequence, ss_pred, output_file):
    with open(output_file, "w") as out:
        for i, (aa, ss) in enumerate(zip(sequence, ss_pred)): #start=1 para que el índice comience en 1, como se espera en I-TASSER.
            if ss != "X": #Solo escribir las líneas que no sean X (es decir, que tengan información de estructura secundaria).
                out.write(f"{i-1} {aa} {ss}\n") #Los separadores son espacios, y el formato es: índice, aminoácido, estructura secundaria.



if __name__ == "__main__":
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    seq, ss = parse_sympred(input_file)

    if len(seq) != len(ss):
        print("Warning: sequence and SS length mismatch!")

    write_itasser_format(seq, ss, output_file)

    print(f"Conversion finished! The finished .txt file: {output_file} can now be used for I-TASSER!")