import os
from multiprocessing.managers import BaseManager
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__, static_url_path='', static_folder='./')
CORS(app)

# initialize manager connection
# NOTE: you might want to handle the password in a less hardcoded way
manager = BaseManager(('', 5602), b'password')
manager.register('query_index')
manager.register('insert_into_index')
manager.register('get_documents_list')
manager.connect()


@app.route("/query", methods=["GET"])
def query_index():
    global manager
    print('QUERY...')
    query_text = request.args.get("text", None)
    if query_text is None:
        return "No text found, please include a ?text=blah parameter in the URL", 400

    response = manager.query_index(query_text)._getvalue()
    print(response)
    response_json = {
        "text": str(response),
        "sources": [{"text": str(x.text),
                     "similarity": round(x.score, 2),
                     "doc_id": str(x.node_id),
                     "start": 0,
                     "end": 0
                    } for x in response.source_nodes]
    }
    return make_response(jsonify(response_json)), 200


@app.route("/uploadFile", methods=["POST"])
def upload_file():

    global manager
    if 'file' not in request.files:
        return "Please send a POST request with a file", 400

    filepath = None
    try:
        uploaded_file = request.files["file"]
        filename = secure_filename(uploaded_file.filename)
        filepath = os.path.join('documents', os.path.basename(filename))
        print('Upload file to:', filepath)
        uploaded_file.save(filepath)

        if request.form.get("filename_as_doc_id", None) is not None:
            manager.insert_into_index(filepath, doc_id=filename)
        else:
            manager.insert_into_index(filepath)
    except Exception as e:
        # cleanup temp file
        if filepath is not None and os.path.exists(filepath):
            os.remove(filepath)
        return "Error: {}".format(str(e)), 500

    # cleanup temp file
    if filepath is not None and os.path.exists(filepath):
        os.remove(filepath)

    return "File inserted!", 200


@app.route("/getDocuments", methods=["GET"])
def get_documents():
    document_list = manager.get_documents_list()._getvalue()

    return make_response(jsonify(document_list)), 200


@app.route("/")
def home():
    return app.send_static_file('index.html')

@app.route('/index/')
def root():
    return app.send_static_file('index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5601, debug=True)

