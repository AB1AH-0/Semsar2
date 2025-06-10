// Load broker offers for customer to accept/reject
function loadBrokerOffers() {
  fetch('/api/inquiries/')
    .then(response => response.json())
    .then(data => {
      const tbody = document.getElementById('broker-offers-tbody');
      const noOffersMessage = document.getElementById('no-broker-offers-message');
      const table = document.getElementById('broker-offers-table');
      
      // Filter only inquiries that have broker responses
      const offersData = data.inquiries ? data.inquiries.filter(inquiry => inquiry.is_accepted && inquiry.broker_post) : [];
      
      if (offersData.length > 0) {
        tbody.innerHTML = '';
        table.style.display = 'table';
        noOffersMessage.style.display = 'none';
        
        offersData.forEach(inquiry => {
          const row = document.createElement('tr');
          
          // Format location
          const location = `${inquiry.city || 'N/A'}${inquiry.area ? ', ' + inquiry.area : ''}`;
          
          // Format property details
          const propertyDetails = `${inquiry.property_type || 'N/A'} - ${inquiry.bedrooms || 'N/A'} BR, ${inquiry.bathrooms || 'N/A'} Bath`;
          
          // Format price range
          let priceRange = 'N/A';
          if (inquiry.min_price && inquiry.max_price) {
            priceRange = `${Number(inquiry.min_price).toLocaleString()} - ${Number(inquiry.max_price).toLocaleString()} EGP`;
          } else if (inquiry.min_price) {
            priceRange = `From ${Number(inquiry.min_price).toLocaleString()} EGP`;
          } else if (inquiry.max_price) {
            priceRange = `Up to ${Number(inquiry.max_price).toLocaleString()} EGP`;
          }
          
          // Format broker offer
          const brokerOffer = `
            <div class="small">
              <strong>Broker:</strong> ${inquiry.broker_post.broker_name}<br>
              <strong>Commission:</strong> ${inquiry.broker_post.commission}%<br>
              <strong>Offered:</strong> ${new Date(inquiry.broker_post.accepted_at).toLocaleDateString()}
              ${inquiry.broker_post.notes ? '<br><strong>Notes:</strong> ' + inquiry.broker_post.notes : ''}
            </div>
          `;
          
          row.innerHTML = `
            <td>${inquiry.id}</td>
            <td><span class="badge bg-${inquiry.transaction_type === 'rent' ? 'primary' : 'success'}">${inquiry.transaction_type}</span></td>
            <td>${location}</td>
            <td>${propertyDetails}</td>
            <td>${priceRange}</td>
            <td>${new Date(inquiry.created_at).toLocaleDateString()}</td>
            <td>${brokerOffer}</td>
            <td>
              <button class="btn btn-success btn-sm me-2 accept-offer-btn" data-inquiry-id="${inquiry.id}" data-broker-name="${inquiry.broker_post.broker_name}">
                <i class="fa fa-check"></i> Accept
              </button>
              <button class="btn btn-danger btn-sm reject-offer-btn" data-inquiry-id="${inquiry.id}" data-broker-name="${inquiry.broker_post.broker_name}">
                <i class="fa fa-times"></i> Reject
              </button>
            </td>
          `;
          
          tbody.appendChild(row);
        });
        
        // Add event listeners for accept/reject buttons
        document.querySelectorAll('.accept-offer-btn').forEach(btn => {
          btn.addEventListener('click', function() {
            const inquiryId = this.getAttribute('data-inquiry-id');
            const brokerName = this.getAttribute('data-broker-name');
            showCustomerResponseModal(inquiryId, brokerName, 'accept');
          });
        });
        
        document.querySelectorAll('.reject-offer-btn').forEach(btn => {
          btn.addEventListener('click', function() {
            const inquiryId = this.getAttribute('data-inquiry-id');
            const brokerName = this.getAttribute('data-broker-name');
            showCustomerResponseModal(inquiryId, brokerName, 'reject');
          });
        });
        
      } else {
        table.style.display = 'none';
        noOffersMessage.style.display = 'block';
      }
    })
    .catch(error => {
      console.error('Error loading broker offers:', error);
      document.getElementById('broker-offers-message-container').innerHTML = 
        '<div class="alert alert-danger">Error loading broker offers. Please refresh the page.</div>';
    });
}

// Show modal for customer response
function showCustomerResponseModal(inquiryId, brokerName, action) {
  const modal = new bootstrap.Modal(document.getElementById('customerResponseModal'));
  const detailsDiv = document.getElementById('broker-offer-details');
  
  detailsDiv.innerHTML = `
    <div class="alert alert-info">
      <h6>Inquiry ID: ${inquiryId}</h6>
      <p><strong>Broker:</strong> ${brokerName}</p>
      <p>You are about to <strong>${action}</strong> this broker's offer.</p>
    </div>
  `;
  
  // Set up modal buttons
  document.getElementById('accept-broker-offer').onclick = function() {
    respondToBrokerOffer(inquiryId, 'accept');
  };
  
  document.getElementById('reject-broker-offer').onclick = function() {
    respondToBrokerOffer(inquiryId, 'reject');
  };
  
  modal.show();
}

// Send customer response to broker offer
function respondToBrokerOffer(inquiryId, action) {
  const notes = document.getElementById('customer-response-notes').value;
  
  const data = {
    inquiry_id: inquiryId,
    action: action,
    customer_notes: notes
  };
  
  fetch('/api/customer-response/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify(data)
  })
  .then(response => response.json())
  .then(result => {
    if (result.success) {
      const modal = bootstrap.Modal.getInstance(document.getElementById('customerResponseModal'));
      modal.hide();
      
      // Show success message
      document.getElementById('broker-offers-message-container').innerHTML = 
        `<div class="alert alert-success">Successfully ${action}ed broker offer!</div>`;
      
      // Refresh the table
      setTimeout(() => {
        loadBrokerOffers();
        document.getElementById('broker-offers-message-container').innerHTML = '';
      }, 2000);
      
    } else {
      alert('Error: ' + (result.error || 'Could not process your response'));
    }
  })
  .catch(error => {
    console.error('Error responding to broker offer:', error);
    alert('Error processing your response. Please try again.');
  });
}
