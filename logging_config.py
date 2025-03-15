import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename="comparison.log",  # Voit vaihtaa tiedoston nimen, jos haluat
    filemode='w',  # Kirjoittaa lokitiedoston aina uudelleen (vaihda 'a' jos haluat lisätä)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Luo globaali loggeri, jota voi käyttää missä tahansa tiedostossa
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Voit vaihtaa ERROR, WARNING, INFO tarpeen mukaan
