<script>
function addToCart(productId) {
    $.ajax({
        url: '/add_to_cart',
        method: 'POST',
        data: { product_id: productId },
        success: function(response) {
            alert('Product added to cart!');
        },
        error: function(error) {
            alert('Error adding product to cart.');
        }
    });
}

function addToWishlist(productId) {
    $.ajax({
        url: '/add_to_wishlist',
        method: 'POST',
        data: { product_id: productId },
        success: function(response) {
            alert('Product added to wishlist!');
        },
        error: function(error) {
            alert('Error adding product to wishlist.');
        }
    });
}
</script>
