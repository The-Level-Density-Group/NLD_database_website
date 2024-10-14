// assets/counter.js

document.addEventListener('DOMContentLoaded', function () {
    console.log('Counter.js loaded');

    function counter_animation() {
        const counter = document.getElementById('dataset_counter');
        console.log('Counter element:', counter);

        if (counter) {
            let targetNumber = parseInt(counter.getAttribute('data-target'), 10);
            console.log('Initial target number:', targetNumber);

            if (isNaN(targetNumber)) {
                console.error('Invalid target number:', counter.getAttribute('data-target'));
                return;
            }

            let currentNumber = 0;
            counter.textContent = currentNumber;

            const increment = Math.ceil(targetNumber / 100);
            const intervalTime = 20;

            const updateCounter = () => {
                currentNumber += increment;

                if (currentNumber >= targetNumber) {
                    counter.textContent = targetNumber;
                    clearInterval(interval);
                    console.log('Reached target number. Interval cleared.');
                } else {
                    counter.textContent = currentNumber;
                    console.log('Current number:', currentNumber);
                }
            };

            let interval = setInterval(updateCounter, intervalTime);

            // Observe changes to the data-target attribute
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'data-target') {
                        // Reset and start animation again
                        targetNumber = parseInt(counter.getAttribute('data-target'), 10);
                        console.log('Updated target number:', targetNumber);
                        if (isNaN(targetNumber)) {
                            console.error('Invalid target number:', counter.getAttribute('data-target'));
                            return;
                        }
                        currentNumber = 0;
                        counter.textContent = currentNumber;
                        clearInterval(interval);
                        interval = setInterval(updateCounter, intervalTime);
                    }
                });
            });

            observer.observe(counter, {
                attributes: true
            });
        } else {
            console.error('Counter element not found.');
        }
    }

    counter_animation();
});
