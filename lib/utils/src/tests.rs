mod utils
{
    #[test]
    fn count()
    {
        const FILE: [&str; 2] = [
            "\t\t\n\t\t\n",
            "\n\n",
        ];
        // Counts characters correctly.
        assert_eq!(crate::string::count(FILE[0], '\t'), 4);
        // Handles absence of characters correctly.
        assert_eq!(crate::string::count(FILE[1], '\t'), 0);
    }
}