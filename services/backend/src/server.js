import express from 'express';

const app = express();
const PORT = 3000;

app.use(express.json());

app.get('/', (_, res) => {
    res.send('<h1>Hello, world!</h1>');
});

app.get('/health', (_, res) => {
    res.json({
        'status': 'healthy'
    })
});

app.listen(PORT, () => {
    console.log(`Server running on ${PORT}`);
})