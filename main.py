from app.app import create_app

if __name__ == "__main__":
    app = create_app(debug=True)
    app.run(host="0.0.0.0", port=5001)
