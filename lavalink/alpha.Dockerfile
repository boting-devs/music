FROM fredboat/lavalink:3.7.4

COPY application.alpha.yml application.yml

USER root

COPY entrypoint.sh ./
ENTRYPOINT ["/bin/sh", "entrypoint.sh"]
CMD ["java", "-Djdk.tls.client.protocols=TLSv1.1,TLSv1.2", "-Xmx2G", "-jar", "Lavalink.jar"]