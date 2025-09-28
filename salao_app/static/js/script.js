function fetchAvailableTimes(date) {
    if (!date) return;
    
    fetch(`/available_times/${date}`)
        .then(response => response.json())
        .then(data => {
            const timeSelect = document.getElementById('time');
            timeSelect.innerHTML = ''; // Clear existing options
            
            if (data.times.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'Nenhum horário disponível';
                option.disabled = true;
                timeSelect.appendChild(option);
            } else {
                data.times.forEach(time => {
                    const option = document.createElement('option');
                    option.value = time;
                    option.textContent = time;
                    timeSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Erro ao buscar horários:', error);
            const timeSelect = document.getElementById('time');
            timeSelect.innerHTML = '<option value="">Erro ao carregar horários</option>';
        });
}

document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('date');
    const today = new Date().toISOString().split('T')[0];
    dateInput.min = today;
    dateInput.value = today; // Prefill with today
    fetchAvailableTimes(today); // Load initial times for today
});
