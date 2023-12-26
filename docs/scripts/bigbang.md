# bigbang.sh

### Description
Runs the necessary commands to start the app. It will leave a running container of the app. Note that it will kill any container that was previously running

### Running the command
To run the command you have to open your terminal on the main directory and run:

`sh scripts/bigbang.sh`

### Examples

Example:

```
git:(main) ✗ ./scripts/bigbang.sh
[+] Running 4/4
 ✔ Container basic-setup-fastapi-1  Removed                                                                                                                                                            0.7s
 ✔ Container fastapi-db             Removed                                                                                                                                                            0.2s
 ✔ Volume basic-setup_db_volume     Removed                                                                                                                                                            0.0s
 ✔ Network basic-setup_default      Removed                                                                                                                                                            0.1s
[+] Building 3.5s (12/12) FINISHED                                                                                                                                                     docker:desktop-linux
 => [fastapi internal] load .dockerignore                                                                                                                                                              0.0s
 => => transferring context: 2B                                                                                                                                                                        0.0s
 => [fastapi internal] load build definition from Dockerfile                                                                                                                                           0.0s
 => => transferring dockerfile: 519B                                                                                                                                                                   0.0s
 => [fastapi internal] load metadata for docker.io/library/python:3.8                                                                                                                                  1.2s
 => [fastapi 1/7] FROM docker.io/library/python:3.8@sha256:7a82536f5a2895b70416ccaffc49e6469d11ed8d9bf6bcfc52328faeae7c7710                                                                            0.0s
 => [fastapi internal] load build context                                                                                                                                                              0.3s
 => => transferring context: 485.93kB                                                                                                                                                                  0.3s
 => CACHED [fastapi 2/7] RUN pip install --upgrade pip                                                                                                                                                 0.0s
 => CACHED [fastapi 3/7] RUN mkdir /app                                                                                                                                                                0.0s
 => CACHED [fastapi 4/7] WORKDIR /app                                                                                                                                                                  0.0s
 => CACHED [fastapi 5/7] COPY requirements.txt .                                                                                                                                                       0.0s
 => CACHED [fastapi 6/7] RUN pip install -r requirements.txt                                                                                                                                           0.0s
 => [fastapi 7/7] COPY . /app                                                                                                                                                                          1.3s
 => [fastapi] exporting to image                                                                                                                                                                       0.7s
 => => exporting layers                                                                                                                                                                                0.7s
 => => writing image sha256:2385e2aa8e635b0121782352eaf4ebf310a63527ce0507ed8caee81fa97c3cb1                                                                                                           0.0s
 => => naming to docker.io/library/fastapi                                                                                                                                                             0.0s
[+] Running 4/4
 ✔ Network basic-setup_default      Created                                                                                                                                                            0.1s
 ✔ Volume "basic-setup_db_volume"   Created                                                                                                                                                            0.0s
 ✔ Container basic-setup-fastapi-1  Started                                                                                                                                                            0.1s
 ✔ Container fastapi-db             Started                                                                                                                                                            0.1s
```