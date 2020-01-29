/// <reference types="Cypress" />

context('Location', () => {
  beforeEach(() => {
    cy.visit('http://test-domain.dev/?account=engineering&region=frankfurt')
  })

  it('cy.hash() - get the current URL hash', () => {
    // https://on.cypress.io/hash
    cy.hash().should('be.empty')
  })

  it('cy.location() - get window.location', () => {
    // https://on.cypress.io/location
    cy.location().should((location) => {
      expect(location.hash).to.be.empty
      expect(location.href).to.eq('http://test-domain.dev/?account=engineering&region=frankfurt')
      expect(location.host).to.eq('test-domain.dev')
      expect(location.hostname).to.eq('test-domain.dev')
      expect(location.origin).to.eq('http://test-domain.dev')
      expect(location.pathname).to.eq('/')
      expect(location.port).to.eq('')
      expect(location.protocol).to.eq('http:')
      expect(location.search).to.be.eq('?account=engineering&region=frankfurt')
    })
  })

  it('cy.url() - get the current URL', () => {
    // https://on.cypress.io/url
    cy.url().should('eq', 'http://test-domain.dev/?account=engineering&region=frankfurt')
  })

  it('.should() - make an assertion about the current subject', () => {
      // https://on.cypress.io/should
      cy.get('#instances-meta')
        .should('have.class', 'badge')
        .should('have.text', 'AWS Account: engineering, Region:  frankfurt')
  })
})
