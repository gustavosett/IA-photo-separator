import tkinter as tk
from tkinter import filedialog, messagebox
import os
import cv2
import numpy as np
import dlib
import threading


class PhotoSeparatorGUI:
    """
    Interface gráfica de seleção de diretorios de fotos
    e aplicar separação com base em reconhecimento facial.
    by @gustavosett #rev 02/04/2023
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Separador de Fotos por Reconhecimento Facial')

        self.input_dir_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()

        self.create_widgets()
        self.arrange_widgets()

        # Carrega o modelo de reconhecimento facial da biblioteca dlib
        try:
            self.facerec = dlib.face_recognition_model_v1(
                os.path.join('dlib_face_recognition_resnet_model_v1.dat'))
        except Exception as e:
            self.print_error(
                'Erro ao carregar modelo de reconhecimento facial', str(e))

    # Abre um dialog para selecionar o diretório de entrada das fotos
    def select_input_dir(self):
        try:
            input_dir = filedialog.askdirectory()
            if input_dir:
                self.input_dir_var.set(input_dir)
                print('Diretório de entrada selecionado:', input_dir)
        except Exception as e:
            self.print_error(
                'Erro ao selecionar diretório de entrada', str(e))

    # Abre um dialog para selecionar o diretório de saída das fotos
    def select_output_dir(self):
        try:
            output_dir = filedialog.askdirectory()
            if output_dir:
                self.output_dir_var.set(output_dir)
                print('Diretório de saída selecionado:', output_dir)
        except Exception as e:
            self.print_error('Erro ao selecionar diretório de saída', str(e))

    # Inicia a execução da separação de fotos em uma nova thread
    def run(self):
        input_dir = self.input_dir_var.get()
        output_dir = self.output_dir_var.get()

        if not self.check_directories(input_dir, output_dir):
            return

        try:
            threading.Thread(target=self.separate_photos, args=(
                input_dir, output_dir)).start()
            print('Finalizou a separação corretamente.')
        except Exception as e:
            self.print_error('Erro ao executar separação de fotos', str(e))

    # Exibe uma mensagem de erro na GUI e imprime no console
    def print_error(self, title, message):
        messagebox.showerror(title, message)
        print(f'{title}: {message}')

    # Verifica se os diretórios de entrada e saída são válidos
    def check_directories(self, input_dir, output_dir):
        try:
            error_messages = [
                ('Por favor, selecione um diretório de entrada.', input_dir),
                ('Por favor, selecione um diretório de saída.', output_dir),
            ]

            for error_message, directory in error_messages:
                if not directory:
                    self.print_error('Erro', error_message)
                    return False

            if input_dir == output_dir:
                self.print_error(
                    'Erro', 'Os diretórios selecionados não podem ser iguais. Por favor, escolha diretórios diferentes.')
                return False

            for directory in [input_dir, output_dir]:
                if not os.path.isdir(directory):
                    self.print_error(
                        'Erro', f'O diretório "{directory}" não é válido. Por favor, selecione um diretório válido.')
                    return False

            return True
        except Exception as e:
            self.print_error('Erro ao verificar os diretórios', str(e))
            return False

    def separate_photos(self, input_dir, output_dir):
        try:
            detector = dlib.get_frontal_face_detector()
            sp = dlib.shape_predictor(os.path.join(os.getcwd(), 'shape_predictor_68_face_landmarks.dat'))
            face_dict = {}
            folder_counter = 0

            persons_folder = os.path.join(output_dir, "PERSONS")
            if not os.path.exists(persons_folder):
                os.makedirs(persons_folder)

            for root, dirs, files in os.walk(input_dir):
                for file in files:
                    if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
                        input_file_path = os.path.join(root, file)
                        img = dlib.load_rgb_image(input_file_path)
                        dets = detector(img, 1)

                        if len(dets) > 0:
                            full_detections = dlib.full_object_detections()

                            for k, d in enumerate(dets):
                                shape = sp(img, d)
                                full_detection = dlib.full_object_detection(
                                    d, shape.parts())
                                full_detections.append(full_detection)

                            for detection in full_detections:
                                face_chip_150 = dlib.get_face_chip(
                                    img, detection, size=150, padding=0.25)

                                found_similar_face = False
                                for folder_name, reference_face in face_dict.items():
                                    if self.compare_faces(reference_face, face_chip_150):
                                        found_similar_face = True
                                        break

                                if not found_similar_face:
                                    folder_counter += 1
                                    folder_name = f'Person_{folder_counter}'
                                    face_dict[folder_name] = face_chip_150

                                    reference_face_path = os.path.join(
                                        persons_folder, f"{folder_name}.png")
                                    dlib.save_image(
                                        face_chip_150, reference_face_path)

                                person_folder_path = os.path.join(
                                    output_dir, folder_name)
                                if not os.path.exists(person_folder_path):
                                    os.makedirs(person_folder_path)

                                output_file_path = os.path.join(
                                    person_folder_path, f"{os.path.splitext(file)[0]}_face_{detection.rect.left()}_{detection.rect.top()}{os.path.splitext(file)[1]}")
                                cv2.imwrite(output_file_path, cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
                                print('\033[1;49;32m' +
                                    f'Face found in {file}!!' + '\033[m')
                        else:
                            print('\033[1;49;31m' +
                                f"No face detected in {file}" + '\033[m')
        except Exception as e:
            self.print_error('Erro ao separar fotos', str(e))

    def compare_faces(self, face1, face2, threshold=0.6):
        """Compara duas faces usando o modelo de reconhecimento facial."""
        try:
            resized_face1 = cv2.resize(face1, (150, 150))
            resized_face2 = cv2.resize(face2, (150, 150))
            face1_descriptor = self.facerec.compute_face_descriptor(
                resized_face1)
            face2_descriptor = self.facerec.compute_face_descriptor(
                resized_face2)

            distance = np.linalg.norm(
                np.array(face1_descriptor) - np.array(face2_descriptor))
            return distance < threshold
        except Exception as e:
            self.print_error('Erro ao comparar faces', str(e))
            return False

    def create_widgets(self):
        self.input_dir_label = tk.Label(
            self.root, text='Diretório de entrada das fotos:')
        self.input_dir_entry = tk.Entry(
            self.root, textvariable=self.input_dir_var)
        self.input_dir_button = tk.Button(
            self.root, text='Selecionar', command=self.select_input_dir)
        self.output_dir_label = tk.Label(
            self.root, text='Diretório de saída das fotos separadas:')
        self.output_dir_entry = tk.Entry(
            self.root, textvariable=self.output_dir_var)
        self.output_dir_button = tk.Button(
            self.root, text='Selecionar', command=self.select_output_dir)
        self.run_button = tk.Button(
            self.root, text='Iniciar separação', command=self.run)

    def arrange_widgets(self):
        self.input_dir_label.grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.input_dir_entry.grid(row=0, column=1, sticky='we', padx=5, pady=5)
        self.input_dir_button.grid(row=0, column=2, sticky='e', padx=5, pady=5)

        self.output_dir_label.grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.output_dir_entry.grid(row=1, column=1, sticky='we', padx=5, pady=5)
        self.output_dir_button.grid(row=1, column=2, sticky='e', padx=5, pady=5)

        self.run_button.grid(row=2, column=0, columnspan=3, pady=5)

    def mainloop(self):
        """Inicia o loop principal da janela."""
        self.root.mainloop()


if __name__ == '__main__':
    app = PhotoSeparatorGUI()
    app.mainloop()
