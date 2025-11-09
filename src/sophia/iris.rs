use std::thread;

#[derive(Debug)]
pub struct Pool {
    size: usize,
}

impl Pool
{
    pub fn new() -> Pool
    {
        Pool{
            size: match thread::available_parallelism() {
                Ok(x) => x.into(),
                Err(_) => 1
            }
        }
    }
}