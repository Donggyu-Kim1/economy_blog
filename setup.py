import os
from config.settings import REPORTS_DIR, IMAGES_DIR


def setup_project():
    """프로젝트 초기 설정을 수행하는 함수"""
    # 1. 필요한 디렉토리 생성
    directories = [
        REPORTS_DIR,
        IMAGES_DIR,
    ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

    # 2. .gitignore 파일 생성 (없는 경우)
    gitignore_path = ".gitignore"
    if not os.path.exists(gitignore_path):
        gitignore_content = """
.env
__pycache__/
*.pyc
.DS_Store
        """.strip()

        with open(gitignore_path, "w") as f:
            f.write(gitignore_content)
        print("Created .gitignore file")

    # 3. .env 파일 생성 (없는 경우)
    env_path = ".env"
    if not os.path.exists(env_path):
        env_content = """
# API Keys
NEWSAPI_KEY=your_api_key_here
        """.strip()

        with open(env_path, "w") as f:
            f.write(env_content)
        print("Created .env file")
        print("Please update your API keys in .env file")


if __name__ == "__main__":
    print("Starting project setup...")
    setup_project()
    print("Setup completed!")
