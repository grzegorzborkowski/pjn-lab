./fast_text/fastText/fasttext supervised -input fake_reviews.train -output model_fake_reviews -epoch 50 -wordNgrams 2 && ./fast_text/fastText/fasttext test model_fake_reviews.bin fake_reviews.valid
