/**
 * Returns a hex code for a color based on num on a 1-10 scale, higher numbers are more green
 * while lower numbers are more red
 * @param {number} num
 * @returns {string} a string containing the hex code for a color 
 */
export function getColor(num) {
    const normalizedNum = (num - 1) / 5;

    const red = Math.floor(255 * (1 - normalizedNum));
    const green = Math.floor(255 * normalizedNum);
    const blue = 0;

    const redHex = red.toString(16).padStart(2, '0');
    const greenHex = green.toString(16).padStart(2, '0');
    const blueHex = blue.toString(16).padStart(2, '0');

    return `#${redHex}${greenHex}${blueHex}`;
}