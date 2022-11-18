FROM fredboat/lavalink:v3.6

COPY application.yml application.yml

USER root

COPY entrypoint.sh ./
ENTRYPOINT ["/bin/sh", "entrypoint.sh"]
CMD ["java", "-Djdk.tls.client.protocols=TLSv1.1,TLSv1.2", "-Xmx2G", "-jar", "Lavalink.jar"]
