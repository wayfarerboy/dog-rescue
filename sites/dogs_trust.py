"""Dogs Trust site checker — uses the GraphQL API."""

from datetime import date

import requests

from .base import Dog, SiteChecker


class DogsTrustChecker(SiteChecker):
    site_name = "Dogs Trust"
    data_file = "dogs-trust.txt"

    API_URL = "https://www.dogstrust.org.uk/api/df-search/graphql"
    PAGE_SIZE = 24

    QUERY = """
    query Search($page: Int!) {
      searchFilterDogs(where: {
        page: $page,
        sort: "NEW",
        age: ["Under 6 months", "6 - 12 months"],
        size: ["Medium", "Small"],
        gender: ["Female"],
        noReserved: true,
        isUnderdog: false,
        liveWithCats: false,
        liveWithDogs: false,
        liveWithPreschool: false,
        liveWithPrimary: false,
        liveWithSecondary: false
      }) {
        totalResults
        results {
          name
          url
          dob
          gender
          breed
          frontEndBreedName
          size
          centreName
          status
        }
      }
    }
    """

    def fetch(self) -> str:
        """Fetch all pages, return combined JSON array string."""
        import json

        all_results: list[dict] = []
        page = 0

        while True:
            payload = {"query": self.QUERY, "variables": {"page": page}}
            resp = requests.post(
                self.API_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            sr = data.get("data", {}).get("searchFilterDogs", {})
            total = sr.get("totalResults", 0)
            results = sr.get("results", [])
            if not results:
                break

            all_results.extend(results)

            page += 1
            if total <= page * self.PAGE_SIZE:
                break

        return json.dumps(all_results)

    def parse(self, raw: str) -> list[Dog]:
        import json

        dogs: list[Dog] = []

        try:
            results = json.loads(raw)
        except json.JSONDecodeError:
            return []

        for d in results:
            name = d.get("name", "")
            dob_str = d.get("dob", "")
            breed = d.get("frontEndBreedName") or d.get("breed", "")
            centre = d.get("centreName", "")
            status = d.get("status", "")
            url = f"https://www.dogstrust.org.uk{d.get('url', '')}"
            gender = "Female" if d.get("gender") == "F" else d.get("gender", "")
            age_str = self._compute_age(dob_str)

            dogs.append(
                Dog(
                    name=name,
                    age=age_str,
                    gender=gender,
                    breed=breed,
                    url=url,
                    status=status,
                    location=centre,
                )
            )

        return dogs

    @staticmethod
    def _compute_age(dob_str: str) -> str:
        """Compute a human-readable age from a YYYY-MM-DD date string."""
        if not dob_str:
            return ""
        try:
            d = date.fromisoformat(dob_str)
            today = date.today()
            months = (today.year - d.year) * 12 + (today.month - d.month)
            if months < 12:
                return f"{months} Months"
            years = months // 12
            return f"{years} Year{'s' if years > 1 else ''} Old"
        except (ValueError, TypeError):
            return dob_str
