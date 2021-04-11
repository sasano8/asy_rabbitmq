# 環境構築

## コンテナ上で開発する
VS-Codeの拡張機能`Remote-Containers`を`Reopen in Container`を実行するとPythonの実行環境コンテナとrabbitmqのコンテナが起動します。
Rabbitmqが利用するポートについては、docker-compose.ymlを参照ください。

## 仮想環境上で開発する
poetryによる仮想環境作成に加え、Rabbitmqへ接続可能（docker-compose.ymlを参照）な状態にしてください。


``` shell
poetry install
```