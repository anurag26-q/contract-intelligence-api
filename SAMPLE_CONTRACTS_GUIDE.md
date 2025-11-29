# Finding Public Sample Contracts

## 📋 Quick Guide: Where to Get 3-5 Public Contract PDFs

You need 3-5 public contract PDFs for testing. Here are the **best legitimate sources**:

### ⭐ Recommended Sources (Easy Download)

#### 1. NASA Standard NDA
- **Link**: https://www.nasa.gov/sites/default/files/atoms/files/nda_template.pdf
- **Type**: Non-Disclosure Agreement
- **Why**: U.S. Government public domain

#### 2. SEC EDGAR Corporate Contracts
- **Link**: https://www.sec.gov/edgar/searchedgar/companysearch.html
- Search for "Material Definitive Agreement"
- **Type**: Commercial agreements (MSAs, Service Agreements)
- **Why**: Publicly filed contracts

#### 3. GitHub Terms of Service
- **Link**: https://docs.github.com/en/site-policy/github-terms/github-terms-of-service
- **Type**: Terms of Service
- **How**: Open link → Print to PDF (Ctrl+P)

#### 4. Docracy Open Legal Documents  
- **Link**: https://www.docracy.com/doc/search?query=NDA
- **Type**: Open-source legal documents
- **Why**: Free, public license agreements

#### 5. World Bank Sample Contracts
- **Link**: https://www.worldbank.org/en/projects-operations/products-and-services/procurement-policies-procedures
- **Type**: Procurement contracts
- **Why**: International public domain

## 🚀 How to Set Up

1. **Download 3-5 PDFs** from sources above
2. **Save to:** `f:\Assignment\sample_contracts\`
3. **Name them clearly:**
   ```
   nda_sample.pdf
   msa_sample.pdf
   tos_sample.pdf
   license_sample.pdf
   agreement_sample.pdf
   ```

## ✅ What Makes a Good Sample

- ✅ Publicly available (no proprietary data)
- ✅ Actual PDF with extractable text
- ✅ Variety of types (NDA, MSA, ToS, etc.)
- ✅ 3-5 files total

## ❌ What to Avoid

- ❌ Real company contracts
- ❌ Contracts with personal information
- ❌ Proprietary/confidential documents

## 🎯 After Adding Files

Test the API:
```bash
make up
curl -X POST http://localhost:8000/api/ingest \
  -F "file=@sample_contracts/nda_sample.pdf"
```

---

**Quick Links:**
- [NASA Contracts](https://www.nasa.gov/offices/procurement/contracts)
- [SEC EDGAR](https://www.sec.gov/edgar/searchedgar/companysearch.html)  
- [Docracy](https://www.docracy.com)
