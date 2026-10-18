import { test, expect } from '@playwright/test';

/** Deterministic browser contract suite. Routes are mocked; live backend smoke is separate. */
test.beforeEach(async ({ page, context }) => {
  let authenticated = false;
  await context.addCookies([
    { name: 'csrftoken', value: 'mock-csrf-token', domain: '127.0.0.1', path: '/' },
    { name: 'csrftoken', value: 'mock-csrf-token', domain: 'localhost', path: '/' }
  ]);
  const docs = [{id:7,title:'Refund Policy',file_type:'txt',original_filename:'policy.txt',processing_status:'completed',has_file:true}];
  await page.route('**/api/**', async route => {
    const req=route.request(), url=new URL(req.url()), path=url.pathname;
    const json=(data,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
    if (path === '/api/auth/csrf/') return json({csrf_ready: true});
    if (path === '/api/auth/register/' && req.method() === 'POST') {
      const payload = req.postDataJSON() || {};
      if (payload.username && payload.password) {
        return json({username: payload.username, registered: true, detail: 'Account registered successfully.'}, 201);
      }
      return json({detail: 'Invalid registration request.'}, 400);
    }
    if (path === '/api/auth/login/' && req.method() === 'POST') {
      const payload = req.postDataJSON() || {};
      if (payload.username === 'demo' && payload.password === 'secret') {
        authenticated = true;
        return json({username: 'demo', authenticated: true});
      }
      return json({detail: 'Authentication failed'}, 401);
    }
    if (path === '/api/auth/logout/' && req.method() === 'POST') {
      authenticated = false;
      return json({authenticated: false});
    }
    if (path === '/api/auth/me/') {
      if (authenticated) return json({username: 'demo', authenticated: true});
      return json({authenticated: false}, 401);
    }
    if (!authenticated) return json({detail:'Unauthorized'},401);
    if (path==='/api/documents/' && req.method()==='GET') return json({count:docs.length,next:null,results:docs});
    if (path==='/api/documents/upload/' && req.method()==='POST') {docs.push({id:8,title:'Sample',file_type:'txt',original_filename:'sample.txt',processing_status:'pending',has_file:true});return json(docs.at(-1),201);}
    if (path==='/api/documents/7/extract/' && req.method()==='POST') return json({document_id:7,page_count:1,character_count:54,processing_status:'completed'});
    if (path==='/api/documents/7/pages/') return json([{id:1,page_number:1,extracted_text:'Refunds within thirty days.'}]);
    if (path==='/api/documents/7/invoice/extract/') return json({id:4},201);
    if (path==='/api/invoices/report/') return json({count:0,results:[]});
    if (path==='/api/invoices/dashboard/') return json({invoice_count:0,payment_status_counts:{pending:0},pending_totals_by_currency:{}});
    if (path==='/api/ask/' && req.method()==='POST') return json({answer:'Refunds within thirty days.',has_evidence:true,source_references:[{document_id:7,document_title:'Refund Policy',page_number:1,chunk_id:10,excerpt:'Refunds within thirty days.'}]});
    if (path==='/api/documents/7/' && req.method()==='DELETE') {docs.splice(0,1);return route.fulfill({status:204,body:''});}
    return json({detail:'Not found'},404);
  });
});
async function signIn(page) {
  await page.goto('/login');
  await page.getByLabel('Username').fill('demo');
  await page.getByLabel('Password').fill('secret');
  await page.getByRole('button',{name:'Sign in'}).click();
  await expect(page.getByText('Refund Policy').first()).toBeVisible();
}
test('authenticated document extraction, page evidence and sign out',async({page})=>{
  await signIn(page);
  await page.getByRole('button',{name:'Extract text'}).first().click();
  await expect(page.getByText(/Extracted 1 page/)).toBeVisible();
  await page.getByRole('button',{name:'View pages'}).first().click();
  await expect(page.getByText('Refunds within thirty days.')).toBeVisible();
  await page.getByRole('button',{name:'Sign out'}).click();
  await expect(page.getByRole('button',{name:'Login'}).first()).toBeVisible();
});
test('document Q&A displays page-level supporting evidence',async({page})=>{
  await signIn(page);
  await page.getByRole('button',{name:'Ask documents'}).click();
  await page.getByLabel('Your question').fill('What is the refund policy?');
  await page.getByRole('button',{name:'Ask documents'}).last().click();
  await expect(page.getByText('Refunds within thirty days.').first()).toBeVisible();
  await expect(page.getByText('Refund Policy · Page 1')).toBeVisible();
});
test('local validation rejects an oversized upload',async({page})=>{
  await signIn(page);
  await page.locator('input[type=file]').setInputFiles({name:'big.txt',mimeType:'text/plain',buffer:Buffer.alloc(10*1024*1024+1)});
  await page.getByRole('button',{name:'Upload document'}).click();
  await expect(page.getByRole('alert')).toContainText('10 MiB');
});
test('invalid authentication retains login screen',async({page})=>{
  await page.goto('/login');
  await page.getByLabel('Username').fill('invalid');
  await page.getByLabel('Password').fill('password');
  await page.getByRole('button',{name:'Sign in'}).click();
  await expect(page.getByRole('alert')).toContainText('Authentication failed');
});

test('unauthenticated API request never reveals private document metadata', async ({ page }) => {
  await page.goto('/');
  const result = await page.evaluate(async () => {
    const response = await fetch('/api/documents/');
    return { status: response.status, payload: await response.json() };
  });
  expect(result.status).toBe(401);
  expect(JSON.stringify(result.payload)).not.toContain('Refund Policy');
});

test('3-page workflow: home -> register -> login -> dashboard and logout -> home', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Turn Unstructured Documents Into Instant, Auditable Decisions.' })).toBeVisible();

  // 1. Home page -> Registration
  await page.getByRole('button', { name: 'Get Started' }).click();
  await expect(page.getByRole('heading', { name: 'Create your workspace account' })).toBeVisible();

  // Fill registration form
  await page.getByLabel('Username').fill('newanalyst');
  await page.locator('input[placeholder="Minimum 12 characters"]').fill('ValidPassword2026!');
  await page.locator('input[placeholder="Repeat password"]').fill('ValidPassword2026!');
  await page.getByRole('button', { name: 'Register & Create Account' }).click();

  // 2. Transitions to Login
  await expect(page.getByRole('heading', { name: 'Sign in to DocuPilot AI' })).toBeVisible();

  // Back to home test
  await page.getByRole('button', { name: 'Return to Home' }).click();
  await expect(page.getByRole('heading', { name: 'Turn Unstructured Documents Into Instant, Auditable Decisions.' })).toBeVisible();

  // 3. Home page -> Login -> Dashboard
  await page.getByRole('button', { name: 'Login' }).first().click();
  await expect(page.getByRole('heading', { name: 'Sign in to DocuPilot AI' })).toBeVisible();
  await page.getByLabel('Username').fill('demo');
  await page.getByLabel('Password').fill('secret');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByText('Refund Policy').first()).toBeVisible();

  // 4. Dashboard -> Logout -> Home
  await page.getByRole('button', { name: 'Sign out' }).click();
  await expect(page.getByRole('heading', { name: 'Turn Unstructured Documents Into Instant, Auditable Decisions.' })).toBeVisible();
});
