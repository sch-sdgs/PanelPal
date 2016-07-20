from flask import Flask

app = Flask(__name__)

@app.route('/PanelPal')
def home():
    return 'Hello, World!'

@app.route('/PanelPal/GetPanel')
def get_panel(panelName):
    return panelName

if __name__ == "__main__":
    app.run(debug=True, host='10.182.131.21')