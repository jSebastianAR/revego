"""
    Copyright (c) 2015.

    Voila Smart Solutions S.C.

    Ruben Valdez Guzman
    Software Developer

    All rights reserved.
"""


from voissemail import VoissEmail

if __name__ == '__main__':
    email = VoissEmail()
    response = email.send(
        "NOTIFICACION - Carta de Recomendacion",
        "dylucx@gmail.com",
        "Carta de Recomendacion",
        "/PATH/TO/FILE/Workbook1.xls")
    print "send email: ", response
