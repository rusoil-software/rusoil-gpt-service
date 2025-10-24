---
name: Service Test Prompt
description: Write Service Test
invokable: true
---

Please write a suite of Jest tests for this service. In the `beforeAll` hook, initialize any services that are needed by calling `Services.get(true)`. In the `beforeEach` hook, clear any tables that need to be cleared before each test. Finally, write the tests themselves. Here's an example:

```typescript
describe("OrganizationSecretService", () => {
  let testOrgId: string;
  let secureKeyValueService: ISecureKeyValueService;

  beforeAll(async () => {
    const services = await Services.get(true);
    secureKeyValueService = services.secureKeyValueService;

    // Create a test organization
    const orgRepo = getAppDataSource().getRepository(Organization);
    const org = orgRepo.create({
      workOsId: "12345",
      name: "Test Organization",
      slug: "test-org",
    });
    const savedOrg = await orgRepo.save(org);
    testOrgId = savedOrg.id;
  });

  beforeEach(async () => {
    // Clear the OrganizationSecret table
    await getAppDataSource().getRepository(OrganizationSecret).clear();
  });

  // ... tests ...
});
```

The tests should be complete, covering any reasonable edge cases, but should not be excessively long. The test file should be adjacent to the service file with the same name, except with a `.test.ts` extension.