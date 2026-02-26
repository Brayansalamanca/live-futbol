import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import compression from 'compression';

const app = express();

// Middleware para comprimir respuestas (más rápido)
app.use(compression());

// Proxy hacia tu servidor Django
app.use('/', createProxyMiddleware({
    target: 'http://localhost:8000', // Aquí corre tu Django
    changeOrigin: true
}));

// Puerto donde escucha Node
const PORT = 3000;
app.listen(PORT, () => {
    console.log(`Servidor Node.js proxy en http://localhost:${PORT}`);
});
