# Data Source Notes

The main dataset is built from the official Bulgarian Sports Totalizator (BST) 6/49 statistics archive.

The importer downloads the annual archive links from the official BST 6/49 statistics page and converts them into `data/historical_draws.csv`.

Important notes:

- The official annual archive files use several different historical text formats.
- The first value of each official draw row is the draw number.
- The following six values are the winning 6/49 combination.
- Some historical years include more than one draw position per draw number, so the project stores `draw_position`.
- Some years include extraordinary draw numbers above 600.
- Exact draw dates are not always available in the yearly official files, so `date` is intentionally left blank for now.

This project uses the data for statistical training and educational analysis only. It does not guarantee lottery predictions.

## Partial 2026 update

The canonical dataset includes a local partial 2026 Toto 6/49 statistics package with 48 draws from 2026-01-04 to 2026-06-18. The year 2026 must be treated as incomplete until a full official yearly archive is available.
