# Panel Field Record

Panel interno con datos de Google Analytics y Meta Ads, actualizado
automaticamente todos los dias por GitHub Actions.

Ver el panel en vivo: (activar GitHub Pages -> queda en
`https://<usuario>.github.io/<repo>/`)

## Secrets necesarios (Settings -> Secrets and variables -> Actions)

- `GA_SERVICE_ACCOUNT_JSON`: contenido completo del JSON de la cuenta de servicio de Google.
- `META_ACCESS_TOKEN`: token de acceso de larga duracion de Meta.
- `META_AD_ACCOUNT_ID`: formato `act_XXXXXXXXXX`.
