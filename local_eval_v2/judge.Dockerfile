FROM csc2108-lcb-judge:v1
# Bound the container itself, including after its host caller is interrupted.
ENTRYPOINT ["timeout", "-k", "2", "175"]
