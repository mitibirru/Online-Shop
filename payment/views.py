from django.shortcuts import render, redirect, get_object_or_404
import braintree
from django.conf import settings
from django.template import context
from orders.models import Order

# instantiate braintree payment gateway
gateway = braintree.BraintreeGateway(settings.BRAINTREE_CONF)

def payment_process(request):
  order_id = request.session.get('order_id')
  order = get_object_or_404(Order, id=order_id)
  total_cost = order.get_total_cost()
  if request.method ==  'POST':
    # retreive nonce
    nonce = request.POST.get('payment_method_nonce', None)
    # create and submit transaction
    result = gateway.transaction.sale({
      'amount': f'{total_cost:.2f}',
      'payment_method_nonce': nonce,
      'options': {
        'submit_for_settlement': True
      }
    })
    if result.is_success:
      # mark the order as paid
      order.paid = True
      # store the unique transaction id
      order.braintree_id = result.transaction.id
      order.save()
      return redirect('payment:done')
    else:
      return redirect('payment:canceled')
  else:
    # generate token
    client_token = gateway.client_token.generate()
    context = {
      'order': order,
      'client_token': client_token
    }
    return render(request, 'payment/process.html', context)

def payment_done(request):
  return render(request, 'payment/done.html')

def payment_canceled(request):
  return redirect(request, 'payment/canceled.html')
  