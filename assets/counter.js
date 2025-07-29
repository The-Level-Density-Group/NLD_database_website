/*
This file is part of The Level Density project website (www.nld.ascsn.net).

The Level Density project website is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

The Level Density project website is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

*/

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
