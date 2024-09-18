// assets/counter.js

function counter_animation() {
    const counter = document.getElementById('dataset_counter');
    console.log('Counter element:', counter);  // Log the counter element to ensure it's found

        // Check if the counter element exists
    if (counter) {
            // Extract the target number from the counter text content
        const targetNumber = parseInt(counter.textContent, 10);
        console.log('Target number:', targetNumber);  // Log the target number
        let currentNumber = 0;  // Initialize the current number to 0

            // Set up an interval to update the counter every 50 milliseconds
        const interval = setInterval(() => {
            currentNumber += 2;  // Increment the current number
            counter.textContent = currentNumber;  // Update the counter text content
            console.log('Current number:', currentNumber);  // Log the current number

                // If the current number reaches the target number, stop the interval
            if (currentNumber >= targetNumber) {
                clearInterval(interval);
                console.log('Reached target number. Interval cleared.');  // Log when the interval is cleared
                }
            }, 3);  // Adjust the speed of the counter as needed
        }
    }
 

document.addEventListener('DOMContentLoaded', function () {
    console.log('Counter.js loaded');  // This log confirms the JS file is loaded

    function startCounter() {

        if (document.readyState == "complete") {
            // const counter = document.getElementById('dataset_counter');
            // console.log('Counter element:', counter);  // Log the counter element to ensure it's found
            counter_animation();
    }

        else {setTimeout(counter_animation, 100)};  // 100 milliseconds delay to ensure the DOM is fully loaded



    } startCounter();
});





