from flask import Flask, render_template

from sections.routes import sections_bp

app = Flask(__name__)
app.register_blueprint(sections_bp)


@app.route('/')
def main():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, port=6433)
