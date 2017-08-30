import logging
import shutil
import configparser
import requests
import lxml
import io

user_config = configparser.ConfigParser()

try:
    import Image
except ImportError:
    from PIL import Image
import pytesseract

from bs4 import BeautifulSoup

pytesseract.pytesseract.tesseract_cmd = 'tesseract'

logging.basicConfig(level=logging.DEBUG)
detran_domain = 'https://www.detran.mg.gov.br'
detran_consulta_url = detran_domain + '/veiculos/situacao-do-veiculo/consulta-a-situacao-do-veiculo'
detran_captcha_url = detran_domain + '/component/servicosmg/servico/-/captcha2/captcha/'
detran_consulta_post_url = detran_domain + '/veiculos/situacao-do-veiculo/consulta-a-situacao-do-veiculo/-/exibe_dados_veiculo/'

user_config.read('settings.cfg')

# Set the third, optional argument of get to 1 if you wish to use raw mode.
placa = user_config.get('Veiculo', 'placa')
chassi = user_config.get('Veiculo', 'chassi') 

with requests.Session() as s:
    res = s.get(detran_consulta_url)
    print(res.cookies)
    response = s.get(detran_captcha_url, stream=True)
    with open('captcha.jpeg', 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    captcha_text = pytesseract.image_to_string(Image.open('captcha.jpeg'))

    logging.info("Captcha text is: %s" % captcha_text)
    payload = {
        'data[ConsultarSituacaoVeiculo][placa]': placa,
        'data[ConsultarSituacaoVeiculo][chassi]': chassi,
        'data[ConsultarSituacaoVeiculo][captcha]': captcha_text
    }

    second_res = s.post(detran_consulta_post_url, data=payload)

    soup = BeautifulSoup(second_res.text, "lxml")

    with io.open('detran.html', 'a', encoding='utf8') as logfile:
        logfile.write(second_res.text)
    

    pendencia = soup.find('span', {"class" : "com-pendencia"})

    if not pendencia:
        logging.info("Veiculo sem pendências")
    else:
        logging.info(pendencia.text)


    vehicle_info = soup.find_all('div', {'class' : 'duas_colunas'})
    
    for info in vehicle_info:
        logging.info(info.text.strip())



