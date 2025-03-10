"""
2024-06-20 tiggi, MY
2025-03-07  MY

Sends mail when the run finished.

RUN:

python 30-sendmail.py -s maria.yli-heikkila@luke.fi

Expects to have a message in: /projappl/project_2013001/agriNDVI/bin/email_contents

"""

import smtplib, ssl
import os
from email.message import EmailMessage

import argparse
import textwrap


def main(args):
    try:
        if not args.email:
            raise Exception('Please give a valid email address. Try --help .')

        print(f'\n\n30-sendmail.py')
        print(f'Sending email to {args.email}')
        
        port = 25  # For SSL
        smtp_server = "smtp.csc.fi"
        sender_email = "myliheik@users.csc.fi"  # Enter your address
        receiver_email = args.email  # Enter receiver address

        SUBJECT = "Uusimmat NDVI-tulokset"

        TEXT = "NDVI-tuloksia valmiina. \nTerveisin,\nMaria"

        with open("/projappl/project_2013001/agriNDVI/bin/email_contents", 'r') as file:
            file_content = file.read()

        # Prepare actual message

        message = """\
        Subject: %s

        %s

        %s
        """ % (SUBJECT, TEXT, file_content)




        print(message)

        # tiggi:
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP(smtp_server, port) as server:
                server.ehlo()  # Can be omitted
                server.starttls(context=context)
                server.ehlo()  # Can be omitted
                #server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.encode('utf-8').strip())

                # alternative:
                #try:
                #   smtpObj = smtplib.SMTP('smtp.pouta.csc.fi')
	        #   smtpObj.sendmail(sender_email, receiver_email, message.encode('utf-8').strip())
            print("Successfully sent email")
        except smtplib.SMTPException:
           print("Error: unable to send email")

            
        print(f'\nDone.')

    except Exception as e:
        print('\n\nUnable to send email. Check prerequisites and see exception output below.')
        parser.print_help()
        raise e


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=textwrap.dedent(__doc__))
    parser.add_argument('-s', '--email',
                        type=str,
                        help='Recipient email address.')
    args = parser.parse_args()
    main(args)
    
