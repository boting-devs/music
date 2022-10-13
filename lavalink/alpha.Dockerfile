FROM fredboat/lavalink:3.5

COPY application.alpha.yml application.yml

USER root

# FIXME: use lavalink stable when available
COPY Lavalink.jar Lavalink.jar

COPY entrypoint.sh ./
ENTRYPOINT ["/bin/sh", "entrypoint.sh"]
CMD ["java", "-Djdk.tls.client.protocols=TLSv1.1,TLSv1.2", "-Xmx1G", "-jar", "Lavalink.jar"]
