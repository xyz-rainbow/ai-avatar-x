document.addEventListener('DOMContentLoaded', () => {
    const expressionTable = document.getElementById('expression-table');
    const subtitleInput = document.getElementById('subtitle-input');
    const sendCommandBtn = document.getElementById('send-command-btn');
    const responseMessage = document.getElementById('response-message');

    const expressions = [
        "neutral", "orgullosa", "angry", "annoyed", "idle1", "idle2", "idle3", "idle4",
        "nervous", "sad", "sleepy", "happy", "thinking", "talking", "wink", "idea",
        "idea2", "curious", "excited"
    ];

    let selectedExpression = 'neutral';

    const columns = 3;
    const rows = Math.ceil(expressions.length / columns);

    for (let i = 0; i < rows; i++) {
        const row = document.createElement('tr');
        for (let j = 0; j < columns; j++) {
            const index = i * columns + j;
            if (index < expressions.length) {
                const cell = document.createElement('td');
                const expression = expressions[index];
                cell.textContent = expression;
                cell.dataset.expression = expression;
                if (expression === selectedExpression) {
                    cell.classList.add('selected');
                }
                cell.addEventListener('click', () => {
                    const currentSelected = document.querySelector('#expression-table .selected');
                    if (currentSelected) {
                        currentSelected.classList.remove('selected');
                    }
                    cell.classList.add('selected');
                    selectedExpression = expression;
                });
                row.appendChild(cell);
            }
        }
        expressionTable.appendChild(row);
    }

    sendCommandBtn.addEventListener('click', async () => {
        const subtitle = subtitleInput.value;

        try {
            const response = await fetch('/api/update_from_gui', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ expression: selectedExpression, subtitle }),
            });

            const result = await response.json();

            if (result.success) {
                responseMessage.textContent = 'Command sent successfully!';
                responseMessage.style.color = 'green';
            } else {
                responseMessage.textContent = `Error: ${result.error}`;
                responseMessage.style.color = 'red';
            }
        } catch (error) {
            responseMessage.textContent = `Error: ${error.message}`;
            responseMessage.style.color = 'red';
        }
    });
});
