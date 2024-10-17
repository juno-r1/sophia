pub fn count(pattern: &str, symbol: char) -> usize
// Counts occurences of a character in a string.
{
    pattern
    .chars()
    .fold(
        0,
        |mut acc: usize, ch: char| {
            match ch {
                x if x == symbol => {acc += 1; acc},
                _ => acc
            }
        }
    )
}