FROM fredboat/lavalink:master-v3.4

COPY application.beta.yml application.yml

ENTRYPOINT ["java", "-Djdk.tls.client.protocols=TLSv1.1,TLSv1.2", "-Xmx1G", "-jar", "Lavalink.jar"]
