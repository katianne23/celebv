import os
import json
import cv2


def download(video_path, ytb_id, proxy=None):
    """
    Baixa um vídeo do YouTube usando yt-dlp.
    
    ytb_id: ID do vídeo no YouTube
    video_path: Caminho para salvar o vídeo
    proxy: URL do proxy (opcional)
    """
    if proxy:
        proxy_cmd = f"--proxy {proxy}"
    else:
        proxy_cmd = ""

    if not os.path.exists(video_path):
        down_video = " ".join([
            "yt-dlp",
            proxy_cmd,
            "--cookies-from-browser chrome",  # Usa cookies do navegador para evitar bloqueios
            '-f', "'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio'",
            '--skip-unavailable-fragments',
            '--merge-output-format', 'mp4',
            f"https://www.youtube.com/watch?v={ytb_id}",
            "--output", video_path,
            "--external-downloader", "aria2c",
            "--external-downloader-args", '"-x 16 -k 1M"'
        ])
        
        print(down_video)
        status = os.system(down_video)

        if status != 0:
            print(f"Erro ao baixar o vídeo: {ytb_id}")


def process_ffmpeg(raw_vid_path, save_folder, save_vid_name, bbox, time):
    """
    Processa um vídeo baixado para cortar e salvar uma parte específica.
    
    raw_vid_path: Caminho do vídeo original
    save_folder: Pasta onde o vídeo recortado será salvo
    save_vid_name: Nome do arquivo salvo
    bbox: Coordenadas de corte (top, bottom, left, right)
    time: Tempo de início e fim (start_sec, end_sec)
    """

    def secs_to_timestr(secs):
        hrs = secs // 3600
        min = (secs % 3600) // 60
        sec = secs % 60
        end = (secs - int(secs)) * 100
        return "{:02d}:{:02d}:{:02d}.{:02d}".format(int(hrs), int(min), int(sec), int(end))

    def expand(bbox, ratio):
        top, bottom = max(bbox[0] - ratio, 0), min(bbox[1] + ratio, 1)
        left, right = max(bbox[2] - ratio, 0), min(bbox[3] + ratio, 1)
        return top, bottom, left, right

    def to_square(bbox):
        top, bottom, leftx, right = bbox
        h = bottom - top
        w = right - leftx
        c = min(h, w) // 2
        c_h = (top + bottom) / 2
        c_w = (leftx + right) / 2
        return c_h - c, c_h + c, c_w - c, c_w + c

    def denorm(bbox, height, width):
        return (
            round(bbox[0] * height),
            round(bbox[1] * height),
            round(bbox[2] * width),
            round(bbox[3] * width)
        )

    out_path = os.path.join(save_folder, save_vid_name)
    cap = cv2.VideoCapture(raw_vid_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    top, bottom, left, right = to_square(denorm(expand(bbox, 0.02), height, width))
    start_sec, end_sec = time

    cmd = f"ffmpeg -i {raw_vid_path} -vf crop=w={right-left}:h={bottom-top}:x={left}:y={top} -ss {secs_to_timestr(start_sec)} -to {secs_to_timestr(end_sec)} -loglevel error {out_path}"
    os.system(cmd)

    return out_path


def load_data(file_path):
    """
    Carrega os dados do JSON contendo informações sobre os vídeos a serem baixados.
    
    file_path: Caminho do arquivo JSON
    """
    with open(file_path) as f:
        data_dict = json.load(f)

    for key, val in data_dict['clips'].items():
        save_name = f"{key}.mp4"
        ytb_id = val['ytb_id']
        time = val['duration']['start_sec'], val['duration']['end_sec']
        bbox = [val['bbox']['top'], val['bbox']['bottom'], val['bbox']['left'], val['bbox']['right']]
        yield ytb_id, save_name, time, bbox


if __name__ == '__main__':
    json_path = 'celebvhq_info.json'  # Caminho do arquivo JSON
    raw_vid_root = './downloaded_celebvhq/raw/'  # Pasta onde os vídeos brutos serão salvos
    processed_vid_root = './downloaded_celebvhq/processed/'  # Pasta onde os vídeos processados serão salvos
    proxy = None  # Proxy opcional

    os.makedirs(raw_vid_root, exist_ok=True)
    os.makedirs(processed_vid_root, exist_ok=True)

    for vid_id, save_vid_name, time, bbox in load_data(json_path):
        raw_vid_path = os.path.join(raw_vid_root, vid_id + ".mp4")
        
        # Primeiro baixa todos os vídeos
        download(raw_vid_path, vid_id, proxy)

        # Depois processa cada um (se necessário)
        # process_ffmpeg(raw_vid_path, processed_vid_root, save_vid_name, bbox, time)

    # Se houver vídeos com erro, tente novamente
    # with open('./ytb_id_errored.log', 'r') as f:
    #     lines = f.readlines()
    # for line in lines:
    #     raw_vid_path = os.path.join(raw_vid_root, line.strip() + ".mp4")
    #     download(raw_vid_path, line.strip())
