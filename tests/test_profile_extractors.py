"""Tests for extract_from_profile methods on site checkers."""

from sites.dogs_trust import DogsTrustChecker
from sites.many_tears import ManyTearsChecker


class TestDogsTrustExtractFromProfile:
    def test_extracts_photo_url_from_carousel(self, tmp_path):
        c = DogsTrustChecker(str(tmp_path))
        html = """
        <html><body>
        <div class="Carousel-module--slide--eb10e">
          <div class="HeroWithCarousel-module--slide--bdbaf">
            <picture>
              <source type="image/webp" srcSet="https://www.dogstrust.org.uk/images/800x600/dogs/3616292/068Sh00000bqo5QIAQ.jpg.webp"/>
              <source srcSet="https://www.dogstrust.org.uk/images/800x600/dogs/3616292/068Sh00000bqo5QIAQ.jpg"/>
              <img src="https://www.dogstrust.org.uk/images/800x600/dogs/3616292/068Sh00000bqo5QIAQ.jpg" alt="Mocha"/>
            </picture>
          </div>
        </div>
        </body></html>
        """
        result = c.extract_from_profile(html)
        assert result["photo_url"] == (
            "https://www.dogstrust.org.uk/images/800x600/dogs/3616292/"
            "068Sh00000bqo5QIAQ.jpg"
        )

    def test_no_carousel_image_returns_empty(self, tmp_path):
        c = DogsTrustChecker(str(tmp_path))
        html = "<html><body><p>No images here</p></body></html>"
        result = c.extract_from_profile(html)
        assert result == {}

    def test_extracts_first_dog_image_only(self, tmp_path):
        """Only the first dog-specific image (with /dogs/ in path) is extracted."""
        c = DogsTrustChecker(str(tmp_path))
        html = """
        <html><body>
        <img src="https://www.dogstrust.org.uk/images/400x300/assets/2022-07/sponsor.jpg" alt="sponsor"/>
        <img src="https://www.dogstrust.org.uk/images/800x600/dogs/3655735/first.jpg" alt="first dog"/>
        <img src="https://www.dogstrust.org.uk/images/800x600/dogs/3655735/second.jpg" alt="second dog"/>
        </body></html>
        """
        result = c.extract_from_profile(html)
        # Should match the src= attribute, first occurrence
        assert "first.jpg" in result.get("photo_url", "")

    def test_ignores_non_dog_images(self, tmp_path):
        """Images not in /images/800x600/dogs/ path are ignored."""
        c = DogsTrustChecker(str(tmp_path))
        html = """
        <html><body>
        <img src="https://www.dogstrust.org.uk/images/400x300/assets/footer-logo.jpg"/>
        </body></html>
        """
        result = c.extract_from_profile(html)
        assert result == {}


class TestManyTearsExtractFromProfile:
    def test_extracts_photo_and_status(self, tmp_path):
        c = ManyTearsChecker(str(tmp_path))
        html = """
        <html><head>
        <meta property="og:image" content="/media/animal_images/Gwen-11-07-26a.jpg.1500x1000_q80_crop_progressive_upscale.jpg" />
        </head><body>
        <h1>Gwen</h1>
        <p>Available for Adoption</p>
        </body></html>
        """
        result = c.extract_from_profile(html)
        assert result["photo_url"] == (
            "https://www.manytearsrescue.org/media/animal_images/"
            "Gwen-11-07-26a.jpg.1500x1000_q80_crop_progressive_upscale.jpg"
        )
        assert result["status"] == "Available for Adoption"

    def test_reserved_status(self, tmp_path):
        c = ManyTearsChecker(str(tmp_path))
        html = """
        <html><head></head><body>
        <p>Reserved</p>
        </body></html>
        """
        result = c.extract_from_profile(html)
        assert result["status"] == "Reserved"

    def test_no_match_returns_empty(self, tmp_path):
        c = ManyTearsChecker(str(tmp_path))
        html = "<html><body><p>No useful info</p></body></html>"
        result = c.extract_from_profile(html)
        assert result == {}

    def test_photo_url_without_og_image(self, tmp_path):
        """No og:image tag → no photo_url extracted."""
        c = ManyTearsChecker(str(tmp_path))
        html = """
        <html><head></head><body>
        <p>Available for Adoption</p>
        </body></html>
        """
        result = c.extract_from_profile(html)
        assert "photo_url" not in result
        assert result["status"] == "Available for Adoption"
