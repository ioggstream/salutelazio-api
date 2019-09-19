# salutelazio API Wrapper

Questa PoC permette di interrogare il sito salutelazio
tramite un API REST che recupera i dati dei medici di base 
e dei pediatri.


## test

Eseguire

  tox

## deploy

L'installazione su GCP avviene col comando

        gcloud functions deploy salutelazio_get --runtime python37 --project salutelazio-api --trigger-http

che restituisce l'URL di interrogazione

        curl -kv https://us-central1-salutelazio-api.cloudfunctions.net/salutelazio_get

### Tecnologia

L'API è basata sul quickstart di Google Cloud Functions

vedi:

* [Cloud Functions Hello World tutorial][tutorial]
* [Cloud Functions Hello World sample source code][code]

[tutorial]: https://cloud.google.com/functions/docs/quickstart
[code]: main.py

