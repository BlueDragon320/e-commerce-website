import os
from app import create_app

env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    port = int(app.config.get('PORT', 8000))
    debug = app.config.get('DEBUG', True)
    print(f"🚀 Starting Noise E-Commerce Site on http://0.0.0.0:{port} (env: {env})")
    print(f"🔗 Ranking Engine URL: {app.config.get('RANKING_ENGINE_URL', 'http://localhost:5000')}")
    app.run(host='0.0.0.0', port=port, debug=debug)
