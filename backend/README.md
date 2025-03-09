# Backend

- Requirements: `poetry==^1.8`, `python==^3.12`, `docker`

## Usage

### Setup dev environment

- TODO: `pgvector` 설치 방법

1. Pull and run postgres container
    ```bash
    docker pull postgres:latest
    docker run -p 5432:5432 --name [your_container_name] \
      -e POSTGRES_PASSWORD=[your_password] \
      -e TZ=Asia/Seoul \
      -v /your/local/directory:/var/lib/postgresql/data \
      -d postgres:latest
    ```

2. Connect to db
    ```bash
    docker exec -it [your_container_name]
    psql -U postgres
    ```

3. Setup db and user
    ```bash
    postgres=# create database [your_db_name];
    postgres=# create role [your_user_name] with login password 'your_user_password';

    postgres=# alter user [your_user_name] with createdb;
    postgres=# alter user [your_user_name] with superuser;

    postgres=# grant all privileges on database [your_db_name] to [your_user_name];
    postgres=# exit;
    ```

4. Clone repository
    ```bash
    git clone https://github.com/myeolinmalchi/PNUME-chat.git
    cd PNUME-chat/backend
    ```

5. Install dependencies
    ```bash
    poetry shell
    poetry install --no-root
    ```

6. Add db info in `.env`
    ```env
    DB_USERNAME=[your_user_name]
    DB_PASSWORD=[your_user_password]
    DB_HOST=[db_host]
    DB_NAME=[your_db_name]
    ```

7. Run `scripts/init_db.py` 
    ```bash
    poetry run python3 scripts/init_db.py
    ```

### Run crawling scripts
- TODO

### Run fastapi server
- TODO
