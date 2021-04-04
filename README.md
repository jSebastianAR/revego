# revego
Docker + revego

## Start project
$ cd docker
$ docker-compose up -d

## Create bd pumpsTest
$ docker exec -it bd sh
$ createdb -U postgres pumpsTest
$ exit

## Create superuser
$ docker exec -it app sh
$ python pumps/manage.py createsuperuser
$ Username: admin
$ Email address: g@mail.com
$ Password: 
$ Password (again):
$ exit

## Restart app
$ docker restart app

## Access to django admin
- go to http:localhost:8080/admin/ and login with the user's credentials you had created before