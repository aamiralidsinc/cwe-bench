<!-- label=GHSA-9rh9-hf3w-9fgg hash=dbd417839d -->
# SYSTEM
You are a Principal Software Quality Assurance (QA) and Defensive Benchmark Architect on the maintainer side of an evaluation platform. We evaluate whether autonomous AI coding agents can correctly REPAIR real-world vulnerabilities (CVE/GHSA) that have already been fixed upstream in open-source projects.

You are provided with:
1. The historical human fix (the "reference patch")
2. The vulnerable codebase at the pre-patch commit
3. Repository maps, manifests, and test fixtures

Your responsibility is to author:
(1) `instruction.md`: A realistic, fair defect report filed by an enterprise user or security auditor.
(2) `hidden_tests.py`: A black-box pytest regression suite checking security enforcement and functional preservation.
(3) Three validation check-patches (shallow, removal, alternative) to prove the test suite accurately distinguishes good repairs from bad ones.

Operational Principles:
- Purely Defensive: All tests offline, inside an isolated container, using harmless sentinels. Tests only assert that invalid/unauthorized input is safely rejected and legitimate operations execute cleanly.
- Strict Fairness: A task is an exam of model intelligence, NOT a guessing game. Every legitimate use the functional suite tests must be an ordinary use of a FEATURE the report names as "must keep working" (name features, not test values).
- Zero Leakage: The agent must discover the faulty code and every place it lives. Never disclose file names, function names, the hidden place(s), or the scope of the bug ("every provider", "on every route").

# REQUEST
# Defect & Vulnerability Metadata
- OSV ID: GHSA-9rh9-hf3w-9fgg
- CVE: CVE-2026-47741
- CWE: CWE-362
- Ecosystem / Package: Packagist / shopper/cart
- Repository: https://github.com/shopperlabs/shopper
- Official Summary: shopper/framework: Race condition on Discount.usage_limit allows silent over-redemption

# Reference Patch (Historical human fix; hidden from evaluated agents)
```diff
diff --git a/packages/admin/src/Livewire/Components/Customers/Addresses.php b/packages/admin/src/Livewire/Components/Customers/Addresses.php
index 8901ee738d89a7d83f2230dd4b2c3c1eb7e29787..1ab5cf5f0166457129da18b89f1ccfb539b9231f 100755
--- a/packages/admin/src/Livewire/Components/Customers/Addresses.php
+++ b/packages/admin/src/Livewire/Components/Customers/Addresses.php
@@ -8,6 +8,7 @@ use Illuminate\Contracts\View\View;
 use Illuminate\Database\Eloquent\Collection;
 use Illuminate\Database\Eloquent\Model;
 use Livewire\Attributes\Computed;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Shopper\Core\Models\Address;
 use Shopper\Core\Models\Contracts\Address as AddressContract;
@@ -19,6 +20,7 @@ class Addresses extends Component
     use HandlesAuthorizationExceptions;
 
     /** @var Model&ShopperUser */
+    #[Locked]
     public ShopperUser $customer;
 
     /**
diff --git a/packages/admin/src/Livewire/Components/Customers/Orders.php b/packages/admin/src/Livewire/Components/Customers/Orders.php
index cb5c43a40a92e4cbdb79bd4b45a26eafc3b7ac0e..eea1838e33a912b5bd3fde561adc0402f013e8bf 100755
--- a/packages/admin/src/Livewire/Components/Customers/Orders.php
+++ b/packages/admin/src/Livewire/Components/Customers/Orders.php
@@ -17,8 +17,11 @@ use Filament\Tables\Filters\SelectFilter;
 use Filament\Tables\Table;
 use Illuminate\Contracts\View\View;
 use Illuminate\Database\Eloquent\Model;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
+use Shopper\Core\Enum\OrderStatus;
+use Shopper\Core\Enum\PaymentStatus;
 use Shopper\Core\Models\Contracts\Order;
 use Shopper\Models\Contracts\ShopperUser;
 use Shopper\Traits\HandlesAuthorizationExceptions;
@@ -31,6 +34,7 @@ class Orders extends Component implements HasActions, HasSchemas, HasTable
     use InteractsWithTable;
 
     /** @var Model&ShopperUser */
+    #[Locked]
     public ShopperUser $customer;
 
     public function table(Table $table): Table
@@ -90,11 +94,11 @@ class Orders extends Component implements HasActions, HasSchemas, HasTable
             ->filters([
                 SelectFilter::make('status')
                     ->label(__('shopper::forms.label.status'))
-                    ->options(\Shopper\Core\Enum\OrderStatus::class)
+                    ->options(OrderStatus::class)
                     ->multiple(),
                 SelectFilter::make('payment_status')
                     ->label(__('shopper::forms.label.payment_status'))
-                    ->options(\Shopper\Core\Enum\PaymentStatus::class)
+                    ->options(PaymentStatus::class)
                     ->multiple(),
                 SelectFilter::make('zone_id')
                     ->label(__('shopper::pages/settings/zones.single'))
diff --git a/packages/admin/src/Livewire/Components/Customers/Profile.php b/packages/admin/src/Livewire/Components/Customers/Profile.php
index 233b79e72bbbae6285dfe6d05a106bac25a7863b..7cca629b15613e6748c2a5a899313e0266ecadc2 100755
--- a/packages/admin/src/Livewire/Components/Customers/Profile.php
+++ b/packages/admin/src/Livewire/Components/Customers/Profile.php
@@ -5,6 +5,7 @@ declare(strict_types=1);
 namespace Shopper\Livewire\Components\Customers;
 
 use Illuminate\Contracts\View\View;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Shopper\Models\Contracts\ShopperUser;
 use Shopper\Traits\HandlesAuthorizationExceptions;
@@ -13,6 +14,7 @@ class Profile extends Component
 {
     use HandlesAuthorizationExceptions;
 
+    #[Locked]
     public ShopperUser $customer;
 
     public function render(): View
diff --git a/packages/admin/src/Livewire/Components/Orders/Fulfillment.php b/packages/admin/src/Livewire/Components/Orders/Fulfillment.php
index dcad8370ddec87d7a0a1aeefdda620ce62a0b738..1ccdd1b567e204969dbee08e44e47f1b59d38a73 100644
--- a/packages/admin/src/Livewire/Components/Orders/Fulfillment.php
+++ b/packages/admin/src/Livewire/Components/Orders/Fulfillment.php
@@ -6,6 +6,7 @@ namespace Shopper\Livewire\Components\Orders;
 
 use BackedEnum;
 use Illuminate\Contracts\View\View;
+use Livewire\Attributes\Locked;
 use Livewire\Attributes\On;
 use Livewire\Component;
 use Shopper\Core\Enum\OrderStatus;
@@ -18,6 +19,7 @@ class Fulfillment extends Component
 {
     use HandlesAuthorizationExceptions;
 
+    #[Locked]
     public Order $order;
 
     public function hasUnfulfilledItems(): bool
diff --git a/packages/admin/src/Livewire/Components/Orders/OrderCustomer.php b/packages/admin/src/Livewire/Components/Orders/OrderCustomer.php
index b77f4e1d1072943ed47fd63eeeac3dd5f2b4559d..dd725580c66f6e738a4a1f128a5b280f4ff8ce66 100644
--- a/packages/admin/src/Livewire/Components/Orders/OrderCustomer.php
+++ b/packages/admin/src/Livewire/Components/Orders/OrderCustomer.php
@@ -6,6 +6,7 @@ namespace Shopper\Livewire\Components\Orders;
 
 use Illuminate\Contracts\View\View;
 use Livewire\Attributes\Computed;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Shopper\Core\Models\Contracts\Order;
 use Shopper\Models\Contracts\ShopperUser;
@@ -18,6 +19,7 @@ class OrderCustomer extends Component
 {
     use HandlesAuthorizationExceptions;
 
+    #[Locked]
     public Order $order;
 
     #[Computed]
diff --git a/packages/admin/src/Livewire/Components/Orders/OrderItems.php b/packages/admin/src/Livewire/Components/Orders/OrderItems.php
index 5cbc10b393b8cc61e008989e5543056cef16012b..49a4df61f2392411e9365ee1d26fcf7a316171ad 100644
--- a/packages/admin/src/Livewire/Components/Orders/OrderItems.php
+++ b/packages/admin/src/Livewire/Components/Orders/OrderItems.php
@@ -5,6 +5,7 @@ declare(strict_types=1);
 namespace Shopper\Livewire\Components\Orders;
 
 use Illuminate\Contracts\View\View;
+use Livewire\Attributes\Locked;
 use Livewire\Attributes\On;
 use Livewire\Component;
 use Livewire\WithPagination;
@@ -16,6 +17,7 @@ class OrderItems extends Component
     use HandlesAuthorizationExceptions;
     use WithPagination;
 
+    #[Locked]
     public Order $order;
 
     public int $perPage = 3;
diff --git a/packages/admin/src/Livewire/Components/Orders/OrderNotes.php b/packages/admin/src/Livewire/Components/Orders/OrderNotes.php
index db15694c29b2302179e0d761b32e7851a7167f69..b37371db03e06680dc6aa6bdf672598a07f70e6f 100644
--- a/packages/admin/src/Livewire/Components/Orders/OrderNotes.php
+++ b/packages/admin/src/Livewire/Components/Orders/OrderNotes.php
@@ -6,6 +6,7 @@ namespace Shopper\Livewire\Components\Orders;
 
 use Filament\Notifications\Notification;
 use Illuminate\Contracts\View\View;
+use Livewire\Attributes\Locked;
 use Livewire\Attributes\Validate;
 use Livewire\Component;
 use Shopper\Core\Events\Orders\OrderNoteAdded;
@@ -16,6 +17,7 @@ class OrderNotes extends Component
 {
     use HandlesAuthorizationExceptions;
 
+    #[Locked]
     public Order $order;
 
     #[Validate('required|string')]
@@ -23,6 +25,8 @@ class OrderNotes extends Component
 
     public function leaveNotes(): void
     {
+        $this->authorize('edit_orders');
+
         $this->validate();
 
         $this->order->update(['notes' => $this->notes]);
diff --git a/packages/admin/src/Livewire/Components/Orders/OrderSummary.php b/packages/admin/src/Livewire/Components/Orders/OrderSummary.php
index 05a913e9477c9be578fbaf78a48d4a780482acf9..9681e710e34b2ef5177bb33153f1a3d07e68cdad 100644
--- a/packages/admin/src/Livewire/Components/Orders/OrderSummary.php
+++ b/packages/admin/src/Livewire/Components/Orders/OrderSummary.php
@@ -5,6 +5,7 @@ declare(strict_types=1);
 namespace Shopper\Livewire\Components\Orders;
 
 use Illuminate\Contracts\View\View;
+use Livewire\Attributes\Locked;
 use Livewire\Attributes\On;
 use Livewire\Component;
 use Shopper\Core\Models\Contracts\Order;
@@ -15,6 +16,7 @@ class OrderSummary extends Component
 {
     use HandlesAuthorizationExceptions;
 
+    #[Locked]
     public Order $order;
 
     #[On('order.updated')]
diff --git a/packages/admin/src/Livewire/Components/Products/Form/Attributes.php b/packages/admin/src/Livewire/Components/Products/Form/Attributes.php
index 3d9026f13c09cb486b8218433979c2a48afc65df..08220f13f3b160ec0e633e83058b8fc8fc12296c 100755
--- a/packages/admin/src/Livewire/Components/Products/Form/Attributes.php
+++ b/packages/admin/src/Livewire/Components/Products/Form/Attributes.php
@@ -17,6 +17,7 @@ use Filament\Tables\Grouping\Group;
 use Filament\Tables\Table;
 use Illuminate\Contracts\View\View;
 use Livewire\Attributes\Lazy;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
 use Shopper\Actions\Store\Product\DetachAttributesToProductAction;
@@ -34,6 +35,7 @@ class Attributes extends Component implements HasActions, HasSchemas, HasTable
     use InteractsWithSchemas;
     use InteractsWithTable;
 
+    #[Locked]
     public Product $product;
 
     public function placeholder(): View
diff --git a/packages/admin/src/Livewire/Components/Products/Form/Edit.php b/packages/admin/src/Livewire/Components/Products/Form/Edit.php
index 87f4bdc86f87d78d3ac3aafd11b8d5efdfa63226..2ea0eecc4d425a4df0bbbf7a9719962dca96d4a0 100755
--- a/packages/admin/src/Livewire/Components/Products/Form/Edit.php
+++ b/packages/admin/src/Livewire/Components/Products/Form/Edit.php
@@ -212,6 +212,8 @@ class Edit extends Component implements HasActions, HasSchemas
 
     public function store(): void
     {
+        $this->authorize('edit_products');
+
         $this->validate();
 
         $this->product = app()->call(UpdateProductAction::class, [
diff --git a/packages/admin/src/Livewire/Components/Products/Form/Files.php b/packages/admin/src/Livewire/Components/Products/Form/Files.php
index 4692c2e68ce28311548786aa80229660d5b2b8e6..a4bec5590e6f7542a29b60b0e28ab4ab7c7c292b 100644
--- a/packages/admin/src/Livewire/Components/Products/Form/Files.php
+++ b/packages/admin/src/Livewire/Components/Products/Form/Files.php
@@ -11,6 +11,7 @@ use Filament\Schemas\Contracts\HasSchemas;
 use Filament\Schemas\Schema;
 use Illuminate\Contracts\View\View;
 use Illuminate\Database\Eloquent\Model;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Shopper\Core\Models\Contracts\Product;
 use Shopper\Traits\HandlesAuthorizationExceptions;
@@ -24,6 +25,7 @@ class Files extends Component implements HasSchemas
     use InteractsWithSchemas;
 
     /** @var Model&Product */
+    #[Locked]
     public Product $product;
 
     /** @var array<string, mixed>|null */
@@ -53,6 +55,8 @@ class Files extends Component implements HasSchemas
 
     public function store(): void
     {
+        $this->authorize('edit_products');
+
         $this->product->update($this->form->getState());
 
         $this->dispatch('product.updated');
diff --git a/packages/admin/src/Livewire/Components/Products/Form/Inventory.php b/packages/admin/src/Livewire/Components/Products/Form/Inventory.php
index d989e70ec02dab892960f2482886936572d0c736..dc0a4bd0ee0bd38cf975fd5a6c796110d5a4369b 100755
--- a/packages/admin/src/Livewire/Components/Products/Form/Inventory.php
+++ b/packages/admin/src/Livewire/Components/Products/Form/Inventory.php
@@ -24,6 +24,7 @@ use Filament\Tables\Grouping\Group;
 use Filament\Tables\Table;
 use Illuminate\Contracts\View\View;
 use Illuminate\Database\Eloquent\Model;
+use Livewire\Attributes\Locked;
 use Livewire\Attributes\On;
 use Livewire\Component;
 use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
@@ -43,6 +44,7 @@ class Inventory extends Component implements HasActions, HasSchemas, HasTable
     use InteractsWithTable;
 
     /** @var Model&Product */
+    #[Locked]
     public Product $product;
 
     /** @var array<string, mixed>|null */
@@ -72,6 +74,7 @@ class Inventory extends Component implements HasActions, HasSchemas, HasTable
                                 TextInput::make('barcode')
                                     ->label(__('shopper::forms.label.barcode'))
                                     ->unique(config('shopper.models.product'), 'barcode', ignoreRecord: true)
+                                    ->regex('/^[A-Za-z0-9\-]*$/')
                                     ->maxLength(255),
                                 TextInput::make('security_stock')
                                     ->label(__('shopper::forms.label.safety_stock'))
@@ -194,6 +197,8 @@ class Inventory extends Component implements HasActions, HasSchemas, HasTable
 
     public function store(): void
     {
+        $this->authorize('edit_products');
+
         $this->product->update($this->form->getState());
 
         $this->dispatch('product.updated');
diff --git a/packages/admin/src/Livewire/Components/Products/Form/Media.php b/packages/admin/src/Livewire/Components/Products/Form/Media.php
index cf68a34edefac2306f91f44770e2698856a82947..34d0da4f0c40e2c3887bc45ec5110ec5456d8437 100755
--- a/packages/admin/src/Livewire/Components/Products/Form/Media.php
+++ b/packages/admin/src/Livewire/Components/Products/Form/Media.php
@@ -11,6 +11,7 @@ use Filament\Schemas\Contracts\HasSchemas;
 use Filament\Schemas\Schema;
 use Illuminate\Contracts\View\View;
 use Illuminate\Database\Eloquent\Model;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Shopper\Core\Models\Contracts\Product;
 use Shopper\Traits\HandlesAuthorizationExceptions;
@@ -24,6 +25,7 @@ class Media extends Component implements HasSchemas
     use InteractsWithSchemas;
 
     /** @var Model&Product */
+    #[Locked]
     public Product $product;
 
     /** @var array<string, mixed>|null */
diff --git a/packages/admin/src/Livewire/Components/Products/Form/RelatedProducts.php b/packages/admin/src/Livewire/Components/Products/Form/RelatedProducts.php
index 3d20a35f41c8d01de8f6bbbf074940b5f7fda663..69f1aedb793650a978b0252bbd70594fe9526280 100755
--- a/packages/admin/src/Livewire/Components/Products/Form/RelatedProducts.php
+++ b/packages/admin/src/Livewire/Components/Products/Form/RelatedProducts.php
@@ -14,6 +14,7 @@ use Illuminate\Contracts\View\View;
 use Illuminate\Database\Eloquent\Model;
 use Livewire\Attributes\Computed;
 use Livewire\Attributes\Lazy;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
 use Shopper\Core\Models\Contracts\Product;
@@ -27,6 +28,7 @@ class RelatedProducts extends Component implements HasActions, HasSchemas
     use InteractsWithSchemas;
 
     /** @var Model&Product */
+    #[Locked]
     public Product $product;
 
     public function mount(): void
diff --git a/packages/admin/src/Livewire/Components/Products/Form/Seo.php b/packages/admin/src/Livewire/Components/Products/Form/Seo.php
index 5da96fa9ea03619dd37852852d82e044195a1a13..ab7eec95ca8d4e020b70c66cceed4ed9dc432c7e 100755
--- a/packages/admin/src/Livewire/Components/Products/Form/Seo.php
+++ b/packages/admin/src/Livewire/Components/Products/Form/Seo.php
@@ -12,6 +12,7 @@ use Filament\Schemas\Contracts\HasSchemas;
 use Filament\Schemas\Schema;
 use Illuminate\Contracts\View\View;
 use Illuminate\Database\Eloquent\Model;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Shopper\Components\Form\SeoField;
 use Shopper\Core\Models\Contracts\Product;
@@ -26,6 +27,7 @@ class Seo extends Component implements HasSchemas
     use InteractsWithSchemas;
 
     /** @var Model&Product */
+    #[Locked]
     public Product $product;
 
     /** @var array<string, mixed>|null */
@@ -51,6 +53,8 @@ class Seo extends Component implements HasSchemas
 
     public function store(): void
     {
+        $this->authorize('edit_products');
+
         $this->product->update($this->form->getState());
 
         $this->dispatch('product.updated');
diff --git a/packages/admin/src/Livewire/Components/Products/Form/Shipping.php b/packages/admin/src/Livewire/Components/Products/Form/Shipping.php
index e25763cd9c181619af40b2cb8899bed1770b6e02..ff534c24b1a33065039e62a068db112fc5fb5cfe 100755
--- a/packages/admin/src/Livewire/Components/Products/Form/Shipping.php
+++ b/packages/admin/src/Livewire/Components/Products/Form/Shipping.php
@@ -11,6 +11,7 @@ use Filament\Schemas\Contracts\HasSchemas;
 use Filament\Schemas\Schema;
 use Illuminate\Contracts\View\View;
 use Illuminate\Database\Eloquent\Model;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Shopper\Components\Form\ShippingField;
 use Shopper\Components\Section;
@@ -26,6 +27,7 @@ class Shipping extends Component implements HasSchemas
     use InteractsWithSchemas;
 
     /** @var Model&Product */
+    #[Locked]
     public Product $product;
 
     /** @var array<string, mixed>|null */
@@ -55,6 +57,8 @@ class Shipping extends Component implements HasSchemas
 
     public function store(): void
     {
+        $this->authorize('edit_products');
+
         $this->product->update($this->form->getState());
 
         $this->dispatch('product.updated');
diff --git a/packages/admin/src/Livewire/Components/Products/Form/Variants.php b/packages/admin/src/Livewire/Components/Products/Form/Variants.php
index 389c7b505c581720bd9b464820be4d63ea1d970c..1d00c60d7acec1639ec754a725a60c6a10742d48 100755
--- a/packages/admin/src/Livewire/Components/Products/Form/Variants.php
+++ b/packages/admin/src/Livewire/Components/Products/Form/Variants.php
@@ -22,6 +22,7 @@ use Illuminate\Database\Eloquent\Collection;
 use Illuminate\Support\Facades\Blade;
 use Illuminate\Support\HtmlString;
 use Livewire\Attributes\Lazy;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
 use Shopper\Core\Models\Contracts\Product;
@@ -36,6 +37,7 @@ class Variants extends Component implements HasActions, HasSchemas, HasTable
     use InteractsWithSchemas;
     use InteractsWithTable;
 
+    #[Locked]
     public Product $product;
 
     public function placeholder(): View
diff --git a/packages/admin/src/Livewire/Components/Settings/Legal/PolicyForm.php b/packages/admin/src/Livewire/Components/Settings/Legal/PolicyForm.php
index b7968fd876cc4b4d7c6ccac292f096e3fb53d863..688f744a99f4e7b070617ea6fd618bc0d77dcf71 100755
--- a/packages/admin/src/Livewire/Components/Settings/Legal/PolicyForm.php
+++ b/packages/admin/src/Livewire/Components/Settings/Legal/PolicyForm.php
@@ -14,6 +14,7 @@ use Filament\Schemas\Concerns\InteractsWithSchemas;
 use Filament\Schemas\Contracts\HasSchemas;
 use Filament\Schemas\Schema;
 use Illuminate\Contracts\View\View;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Shopper\Core\Models\Legal;
 use Shopper\Traits\HandlesAuthorizationExceptions;
@@ -27,6 +28,7 @@ class PolicyForm extends Component implements HasActions, HasSchemas
     use InteractsWithActions;
     use InteractsWithSchemas;
 
+    #[Locked]
     public Legal $legal;
 
     /**
@@ -59,6 +61,8 @@ class PolicyForm extends Component implements HasActions, HasSchemas
 
     public function store(): void
     {
+        $this->authorize('access_setting');
+
         $this->legal->update(array_merge($this->form->getState(), [
             'slug' => $this->legal->slug,
         ]));
diff --git a/packages/admin/src/Livewire/Components/Settings/Legal/Privacy.php b/packages/admin/src/Livewire/Components/Settings/Legal/Privacy.php
index 37b2360e1d0dbf7858cb33178b15b3f02a24d197..4465e4e925a8b3ebd99d2e9d220841d1674b1bd0 100755
--- a/packages/admin/src/Livewire/Components/Settings/Legal/Privacy.php
+++ b/packages/admin/src/Livewire/Components/Settings/Legal/Privacy.php
@@ -5,6 +5,7 @@ declare(strict_types=1);
 namespace Shopper\Livewire\Components\Settings\Legal;
 
 use Illuminate\Contracts\View\View;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Shopper\Core\Models\Legal;
 use Shopper\Traits\HandlesAuthorizationExceptions;
@@ -13,6 +14,7 @@ class Privacy extends Component
 {
     use HandlesAuthorizationExceptions;
 
+    #[Locked]
     public Legal $legal;
 
     public function render(): View
diff --git a/packages/admin/src/Livewire/Components/Settings/Legal/Refund.php b/packages/admin/src/Livewire/Components/Settings/Legal/Refund.php
index 90c6b3f636645400ad9b9b44494b44712bbd9bd4..1a95bbeec7d5abd28d2ec3493b9825f93308c30b 100755
--- a/packages/admin/src/Livewire/Components/Settings/Legal/Refund.php
+++ b/packages/admin/src/Livewire/Components/Settings/Legal/Refund.php
@@ -5,6 +5,7 @@ declare(strict_types=1);
 namespace Shopper\Livewire\Components\Settings\Legal;
 
 use Illuminate\Contracts\View\View;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Shopper\Core\Models\Legal;
 use Shopper\Traits\HandlesAuthorizationExceptions;
@@ -13,6 +14,7 @@ class Refund extends Component
 {
     use HandlesAuthorizationExceptions;
 
+    #[Locked]
     public Legal $legal;
 
     public function render(): View
diff --git a/packages/admin/src/Livewire/Components/Settings/Legal/Shipping.php b/packages/admin/src/Livewire/Components/Settings/Legal/Shipping.php
index 83af6d4280534594eaa58b64ac861c02a673655c..8e409418514069a29179bcd31718b4a0b7a322ec 100755
--- a/packages/admin/src/Livewire/Components/Settings/Legal/Shipping.php
+++ b/packages/admin/src/Livewire/Components/Settings/Legal/Shipping.php
@@ -5,6 +5,7 @@ declare(strict_types=1);
 namespace Shopper\Livewire\Components\Settings\Legal;
 
 use Illuminate\Contracts\View\View;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Shopper\Core\Models\Legal;
 use Shopper\Traits\HandlesAuthorizationExceptions;
@@ -13,6 +14,7 @@ class Shipping extends Component
 {
     use HandlesAuthorizationExceptions;
 
+    #[Locked]
     public Legal $legal;
 
     public function render(): View
diff --git a/packages/admin/src/Livewire/Components/Settings/Legal/Terms.php b/packages/admin/src/Livewire/Components/Settings/Legal/Terms.php
index be641d33530580086576900825cbe0b05ca8a0de..967fb0535a7c8faa4838577fcbfcffd466d976e2 100755
--- a/packages/admin/src/Livewire/Components/Settings/Legal/Terms.php
+++ b/packages/admin/src/Livewire/Components/Settings/Legal/Terms.php
@@ -5,6 +5,7 @@ declare(strict_types=1);
 namespace Shopper\Livewire\Components\Settings\Legal;
 
 use Illuminate\Contracts\View\View;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Shopper\Core\Models\Legal;
 use Shopper\Traits\HandlesAuthorizationExceptions;
@@ -13,6 +14,7 @@ class Terms extends Component
 {
     use HandlesAuthorizationExceptions;
 
+    #[Locked]
     public Legal $legal;
 
     public function render(): View
diff --git a/packages/admin/src/Livewire/Components/Settings/Locations/InventoryForm.php b/packages/admin/src/Livewire/Components/Settings/Locations/InventoryForm.php
index 85079e124f071ad38a15afa034b49eca0677e008..f5b726f80b31d06affb8780e3ec6e9dc3effdd90 100755
--- a/packages/admin/src/Livewire/Components/Settings/Locations/InventoryForm.php
+++ b/packages/admin/src/Livewire/Components/Settings/Locations/InventoryForm.php
@@ -18,6 +18,7 @@ use Filament\Schemas\Schema;
 use Illuminate\Contracts\View\View;
 use Illuminate\Database\Eloquent\Model;
 use Illuminate\Support\Str;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Shopper\Components\Form\AddressField;
 use Shopper\Components\Section;
@@ -34,6 +35,7 @@ class InventoryForm extends Component implements HasActions, HasSchemas
     use InteractsWithActions;
     use InteractsWithSchemas;
 
+    #[Locked]
     public Model&Inventory $inventory;
 
     /** @var array<string, mixed>|null */
@@ -102,6 +104,8 @@ class InventoryForm extends Component implements HasActions, HasSchemas
 
     public function store(): void
     {
+        $this->authorize($this->inventory->id ? 'edit_inventories' : 'add_inventories');
+
         if ($this->inventory->id) {
             $this->inventory->update($this->form->getState());
         } else {
diff --git a/packages/admin/src/Livewire/Components/Settings/Team/Permissions.php b/packages/admin/src/Livewire/Components/Settings/Team/Permissions.php
index 65937fed1d9e2ac0aaccd196297b800dfa8c22aa..240ad15d15aebe284c9248dc3ff691e29bb5fcb1 100755
--- a/packages/admin/src/Livewire/Components/Settings/Team/Permissions.php
+++ b/packages/admin/src/Livewire/Components/Settings/Team/Permissions.php
@@ -6,6 +6,7 @@ namespace Shopper\Livewire\Components\Settings\Team;
 
 use Filament\Notifications\Notification;
 use Illuminate\Contracts\View\View;
+use Livewire\Attributes\Locked;
 use Livewire\Attributes\On;
 use Livewire\Component;
 use Shopper\Models\Permission;
@@ -16,6 +17,7 @@ class Permissions extends Component
 {
     use HandlesAuthorizationExceptions;
 
+    #[Locked]
     public Role $role;
 
     public function mount(): void
@@ -26,9 +28,13 @@ class Permissions extends Component
     public function togglePermission(int $id): void
     {
         $this->authorize('view_users');
-        /** @var Permission $permission */
+
         $permission = Permission::query()->find($id);
 
+        if ($permission === null) {
+            return;
+        }
+
         if ($this->role->hasPermissionTo($permission->name)) {
             $this->role->revokePermissionTo($permission->name);
 
@@ -50,7 +56,13 @@ class Permissions extends Component
     {
         $this->authorize('view_users');
 
-        Permission::query()->find($id)->delete();
+        $permission = Permission::query()->find($id);
+
+        if ($permission === null) {
+            return;
+        }
+
+        $permission->delete();
 
         Notification::make()
             ->title(__('shopper::notifications.delete', ['item' => __('shopper::pages/settings/staff.permission')]))
diff --git a/packages/admin/src/Livewire/Components/Settings/Team/UsersRole.php b/packages/admin/src/Livewire/Components/Settings/Team/UsersRole.php
index 707368a782b6b0415d84bf952c0e503fef57e835..3a3be81ede076fbdb1e152a1e858f98296d39edb 100755
--- a/packages/admin/src/Livewire/Components/Settings/Team/UsersRole.php
+++ b/packages/admin/src/Livewire/Components/Settings/Team/UsersRole.php
@@ -16,6 +16,7 @@ use Filament\Tables\Contracts\HasTable;
 use Filament\Tables\Table;
 use Illuminate\Contracts\View\View;
 use Illuminate\Database\Eloquent\Builder;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Shopper\Models\Contracts\ShopperUser;
 use Shopper\Models\Role;
@@ -28,6 +29,7 @@ class UsersRole extends Component implements HasActions, HasSchemas, HasTable
     use InteractsWithSchemas;
     use InteractsWithTable;
 
+    #[Locked]
     public Role $role;
 
     public function table(Table $table): Table
diff --git a/packages/admin/src/Livewire/Pages/Collection/Edit.php b/packages/admin/src/Livewire/Pages/Collection/Edit.php
index 50d3789a9d8d4e3e07ce3ff35107df35893e6052..ffb0bc1e3976f789e0fe6941e8db4635a9d4a46f 100755
--- a/packages/admin/src/Livewire/Pages/Collection/Edit.php
+++ b/packages/admin/src/Livewire/Pages/Collection/Edit.php
@@ -133,6 +133,8 @@ class Edit extends AbstractPageComponent implements HasActions, HasSchemas
 
     public function store(): void
     {
+        $this->authorize('edit_collections');
+
         $this->collection->update($this->form->getState());
 
         Notification::make()
diff --git a/packages/admin/src/Livewire/Pages/Customers/Create.php b/packages/admin/src/Livewire/Pages/Customers/Create.php
index d1d473171136abc53f6342a63bd52092bc36de33..0fe2967cf7e18b3ec6e91ac26ccdca6d84537a37 100755
--- a/packages/admin/src/Livewire/Pages/Customers/Create.php
+++ b/packages/admin/src/Livewire/Pages/Customers/Create.php
@@ -141,12 +141,23 @@ class Create extends AbstractPageComponent implements HasActions, HasSchemas
 
     public function store(): void
     {
+        $this->authorize('add_customers');
+
         /** @var array<string, mixed> $data */
         $data = $this->form->getState();
         $sendMail = data_get($data, 'send_mail');
         $password = data_get($data, 'password_confirmation');
 
-        $customerData = Arr::except($data, ['address', 'send_mail', 'password_confirmation']);
+        $customerData = Arr::only($data, [
+            'first_name',
+            'last_name',
+            'email',
+            'phone_number',
+            'gender',
+            'password',
+            'opt_in',
+        ]);
+
         $address = array_merge(Arr::only($data, ['address'])['address'], [
             'first_name' => $data['first_name'],
             'last_name' => $data['last_name'],
diff --git a/packages/admin/src/Livewire/Pages/Customers/Show.php b/packages/admin/src/Livewire/Pages/Customers/Show.php
index dc058f9730397df104cf3abfaf34d5e8983c3a3d..58bb4ceab584e6fcdd55d31278ec03c663cb502d 100755
--- a/packages/admin/src/Livewire/Pages/Customers/Show.php
+++ b/packages/admin/src/Livewire/Pages/Customers/Show.php
@@ -13,6 +13,7 @@ use Filament\Schemas\Contracts\HasSchemas;
 use Illuminate\Contracts\View\View;
 use Illuminate\Database\Eloquent\Model;
 use Illuminate\Support\Str;
+use Livewire\Attributes\Locked;
 use Livewire\Attributes\Url;
 use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
 use Shopper\Livewire\Pages\AbstractPageComponent;
@@ -25,6 +26,7 @@ class Show extends AbstractPageComponent implements HasActions, HasSchemas
     use InteractsWithActions;
     use InteractsWithSchemas;
 
+    #[Locked]
     public ShopperUser $customer;
 
     #[Url(as: 'tab')]
diff --git a/packages/admin/src/Livewire/Pages/Order/Detail.php b/packages/admin/src/Livewire/Pages/Order/Detail.php
index 380dcc3f95ae55cf0e69f7f6bf869f27fc0b3ea5..0c27131dcd15f45e2214def779f2994fc7effc64 100755
--- a/packages/admin/src/Livewire/Pages/Order/Detail.php
+++ b/packages/admin/src/Livewire/Pages/Order/Detail.php
@@ -11,6 +11,7 @@ use Filament\Notifications\Notification;
 use Filament\Schemas\Concerns\InteractsWithSchemas;
 use Filament\Schemas\Contracts\HasSchemas;
 use Illuminate\Contracts\View\View;
+use Livewire\Attributes\Locked;
 use Livewire\Attributes\On;
 use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
 use Shopper\Core\Enum\OrderStatus;
@@ -30,6 +31,7 @@ class Detail extends AbstractPageComponent implements HasActions, HasSchemas
     use InteractsWithActions;
     use InteractsWithSchemas;
 
+    #[Locked]
     public Order $order;
 
     public function mount(): void
@@ -48,6 +50,7 @@ class Detail extends AbstractPageComponent implements HasActions, HasSchemas
     {
         return Action::make('cancelOrder')
             ->label(__('shopper::forms.actions.cancel_order'))
+            ->authorize('edit_orders')
             ->visible($this->order->canBeCancelled())
             ->action(function (): void {
                 $this->order->update([
@@ -71,6 +74,7 @@ class Detail extends AbstractPageComponent implements HasActions, HasSchemas
     {
         return Action::make('startProcessing')
             ->label(__('shopper::forms.actions.start_processing'))
+            ->authorize('edit_orders')
             ->visible($this->order->isNew())
             ->action(function (): void {
                 $this->order->update(['status' => OrderStatus::Processing]);
@@ -89,6 +93,7 @@ class Detail extends AbstractPageComponent implements HasActions, HasSchemas
     {
         return Action::make('markPaid')
             ->label(__('shopper::forms.actions.mark_paid'))
+            ->authorize('edit_orders')
             ->visible($this->order->isPaymentPending() || $this->order->isPaymentAuthorized())
             ->action(function (): void {
                 $data = ['payment_status' => PaymentStatus::Paid];
@@ -115,6 +120,7 @@ class Detail extends AbstractPageComponent implements HasActions, HasSchemas
     {
         return Action::make('markComplete')
             ->label(__('shopper::forms.actions.mark_complete'))
+            ->authorize('edit_orders')
             ->visible($this->order->isProcessing() && $this->order->isPaid())
             ->action(function (): void {
                 $this->order->update(['status' => OrderStatus::Completed]);
@@ -136,6 +142,7 @@ class Detail extends AbstractPageComponent implements HasActions, HasSchemas
         return Action::make('capturePayment')
             ->label(__('shopper::forms.actions.capture_payment'))
             ->icon(Untitledui::CreditCardDown)
+            ->authorize('edit_orders')
             ->visible($this->order->isPaymentAuthorized())
             ->requiresConfirmation()
             ->modalIcon(Untitledui::CreditCardDown)
@@ -182,6 +189,7 @@ class Detail extends AbstractPageComponent implements HasActions, HasSchemas
             ->label(__('shopper::forms.actions.archive'))
             ->color('danger')
             ->icon(Untitledui::Archive)
+            ->authorize('edit_orders')
             ->visible(! $this->order->isCompleted() && ! $this->order->isPaid())
             ->requiresConfirmation()
             ->modalHeading(__('shopper::pages/orders.modals.archived_number', ['number' => $this->order->number]))
diff --git a/packages/admin/src/Livewire/Pages/Order/Shipments.php b/packages/admin/src/Livewire/Pages/Order/Shipments.php
index 8c6c22cffaa2a94b4522cb9e36b5801b33231c49..2572a2323542cf0780ee1cb59d862de43ead0334 100644
--- a/packages/admin/src/Livewire/Pages/Order/Shipments.php
+++ b/packages/admin/src/Livewire/Pages/Order/Shipments.php
@@ -137,6 +137,7 @@ class Shipments extends AbstractPageComponent implements HasActions, HasSchemas,
                     ->label(__('shopper::forms.actions.mark_delivered'))
                     ->icon(Untitledui::PackageCheck)
                     ->color('success')
+                    ->authorize('edit_orders')
                     ->visible(fn (OrderShipping $record): bool => $record->canBeDelivered())
                     ->requiresConfirmation()
                     ->action(function (OrderShipping $record): void {
@@ -151,6 +152,7 @@ class Shipments extends AbstractPageComponent implements HasActions, HasSchemas,
                     ->label(__('shopper::forms.actions.edit'))
                     ->icon(Untitledui::Edit03)
                     ->iconButton()
+                    ->authorize('edit_orders')
                     ->modalWidth(Width::Large)
                     ->fillForm(fn (OrderShipping $record): array => [
                         'carrier_id' => $record->carrier_id,
diff --git a/packages/admin/src/Livewire/Pages/Product/Edit.php b/packages/admin/src/Livewire/Pages/Product/Edit.php
index 79ab241efea986ede28ff17d6be7637de69d28e6..dddd17a14cd7223b1566e27baab4230eb4b23989 100755
--- a/packages/admin/src/Livewire/Pages/Product/Edit.php
+++ b/packages/admin/src/Livewire/Pages/Product/Edit.php
@@ -12,6 +12,7 @@ use Filament\Schemas\Concerns\InteractsWithSchemas;
 use Filament\Schemas\Contracts\HasSchemas;
 use Illuminate\Contracts\View\View;
 use Illuminate\Database\Eloquent\Model;
+use Livewire\Attributes\Locked;
 use Livewire\Attributes\On;
 use Livewire\Attributes\Url;
 use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
@@ -27,6 +28,7 @@ class Edit extends AbstractPageComponent implements HasActions, HasSchemas
     use InteractsWithSchemas;
 
     /** @var Model&ProductContract */
+    #[Locked]
     public ProductContract $product;
 
     #[Url(as: 'tab')]
diff --git a/packages/admin/src/Livewire/Pages/Product/Variant.php b/packages/admin/src/Livewire/Pages/Product/Variant.php
index cccf9a4b4a4523b68e53883ac06d94d5d3a7be36..68a78068c9c3723addff6109b3c44c026cc9feae 100755
--- a/packages/admin/src/Livewire/Pages/Product/Variant.php
+++ b/packages/admin/src/Livewire/Pages/Product/Variant.php
@@ -48,6 +48,7 @@ class Variant extends AbstractPageComponent implements HasActions, HasSchemas
         return Action::make('updateStock')
             ->label(__('shopper::forms.actions.edit'))
             ->color('gray')
+            ->authorize('edit_products')
             ->modalWidth(Width::Large)
             ->fillForm([
                 'sku' => $this->variant->sku,
@@ -67,6 +68,7 @@ class Variant extends AbstractPageComponent implements HasActions, HasSchemas
                 TextInput::make('barcode')
                     ->label(__('shopper::forms.label.barcode'))
                     ->unique(config('shopper.models.variant'), 'barcode', ignoreRecord: true)
+                    ->regex('/^[A-Za-z0-9\-]*$/')
                     ->maxLength(255),
             ])
             ->action(function (array $data): void {
diff --git a/packages/admin/src/Livewire/Pages/Settings/Carriers.php b/packages/admin/src/Livewire/Pages/Settings/Carriers.php
index d6a166266b997cb461f03a0de35428933d968885..e014a869e0a9d692eadb3da648266c92a40010d9 100644
--- a/packages/admin/src/Livewire/Pages/Settings/Carriers.php
+++ b/packages/admin/src/Livewire/Pages/Settings/Carriers.php
@@ -50,6 +50,7 @@ class Carriers extends Component implements HasActions, HasSchemas, HasTable
     {
         return Action::make('createCarrier')
             ->label(__('shopper::pages/settings/carriers.add_carrier'))
+            ->authorize('access_setting')
             ->modalWidth(Width::ExtraLarge)
             ->modalHeading(__('shopper::pages/settings/carriers.add_carrier'))
             ->modalSubmitActionLabel(__('shopper::forms.actions.save'))
@@ -88,7 +89,8 @@ class Carriers extends Component implements HasActions, HasSchemas, HasTable
                         default => 'warning',
                     }),
                 ToggleColumn::make('is_enabled')
-                    ->label(__('shopper::forms.label.status')),
+                    ->label(__('shopper::forms.label.status'))
+                    ->beforeStateUpdated(fn (): mixed => $this->authorize('access_setting')),
                 TextColumn::make('updated_at')
                     ->label(__('shopper::forms.label.updated_at'))
                     ->date(),
@@ -98,12 +100,14 @@ class Carriers extends Component implements HasActions, HasSchemas, HasTable
                     ->label(__('shopper::forms.actions.edit'))
                     ->icon(Untitledui::Edit03)
                     ->iconButton()
+                    ->authorize('access_setting')
                     ->modalWidth(Width::ExtraLarge)
                     ->schema($this->getCarrierFormSchema())
                     ->successNotificationTitle(__('shopper::notifications.carrier.update')),
                 DeleteAction::make('delete')
                     ->label(__('shopper::forms.actions.delete'))
                     ->icon(Untitledui::Trash03)
+                    ->authorize('access_setting')
                     ->iconButton(),
             ])
             ->emptyStateIcon(Untitledui::Truck)
diff --git a/packages/admin/src/Livewire/Pages/Settings/Currencies.php b/packages/admin/src/Livewire/Pages/Settings/Currencies.php
index 7107eb00d4f9f066a085696044002c94411b87c4..7a18f17b4872ad4adddd50306d0431ef4edaadc5 100644
--- a/packages/admin/src/Livewire/Pages/Settings/Currencies.php
+++ b/packages/admin/src/Livewire/Pages/Settings/Currencies.php
@@ -61,13 +61,15 @@ class Currencies extends Component implements HasActions, HasSchemas, HasTable
                     ->numeric(decimalPlaces: 4)
                     ->sortable(),
                 ToggleColumn::make('is_enabled')
-                    ->label(__('shopper::forms.label.status')),
+                    ->label(__('shopper::forms.label.status'))
+                    ->beforeStateUpdated(fn (): mixed => $this->authorize('access_setting')),
             ])
             ->recordActions([
                 EditAction::make('edit')
                     ->label(__('shopper::forms.actions.edit'))
                     ->icon(Untitledui::Edit03)
                     ->iconButton()
+                    ->authorize('access_setting')
                     ->modalHeading(__('shopper::pages/settings/currencies.edit_rate'))
                     ->modalWidth(Width::Large)
                     ->schema([
@@ -91,6 +93,7 @@ class Currencies extends Component implements HasActions, HasSchemas, HasTable
                     ->icon(Untitledui::CheckVerified)
                     ->modalIcon(Untitledui::CheckVerified)
                     ->modalIconColor('success')
+                    ->authorize('access_setting')
                     ->requiresConfirmation()
                     ->action(function (Collection $records): void {
                         Currency::withoutGlobalScopes()
@@ -108,6 +111,7 @@ class Currencies extends Component implements HasActions, HasSchemas, HasTable
                 BulkAction::make('disable')
                     ->label(__('shopper::forms.actions.disable'))
                     ->icon(Untitledui::SlashCircle01)
+                    ->authorize('access_setting')
                     ->requiresConfirmation()
                     ->color('warning')
                     ->action(function (Collection $records): void {
diff --git a/packages/admin/src/Livewire/Pages/Settings/Locations/Edit.php b/packages/admin/src/Livewire/Pages/Settings/Locations/Edit.php
index 50da0a2a6b94461425ee4527e9b761d151bd716d..0a23e5258f076f04130d41fb51b67041d1143c78 100755
--- a/packages/admin/src/Livewire/Pages/Settings/Locations/Edit.php
+++ b/packages/admin/src/Livewire/Pages/Settings/Locations/Edit.php
@@ -6,6 +6,7 @@ namespace Shopper\Livewire\Pages\Settings\Locations;
 
 use Illuminate\Contracts\View\View;
 use Livewire\Attributes\Layout;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Shopper\Core\Models\Inventory;
 use Shopper\Traits\HandlesAuthorizationExceptions;
@@ -15,6 +16,7 @@ class Edit extends Component
 {
     use HandlesAuthorizationExceptions;
 
+    #[Locked]
     public Inventory $inventory;
 
     public function mount(): void
diff --git a/packages/admin/src/Livewire/Pages/Settings/PaymentMethods.php b/packages/admin/src/Livewire/Pages/Settings/PaymentMethods.php
index 445bc614169cdb3b1fd119d3f1edbdc1a8c37cbd..76dc566fc22cefbcdc0f605cc8ea1d27f2ada12a 100644
--- a/packages/admin/src/Livewire/Pages/Settings/PaymentMethods.php
+++ b/packages/admin/src/Livewire/Pages/Settings/PaymentMethods.php
@@ -50,6 +50,7 @@ class PaymentMethods extends Component implements HasActions, HasSchemas, HasTab
     {
         return Action::make('createPayment')
             ->label(__('shopper::pages/settings/payments.add_payment'))
+            ->authorize('access_setting')
             ->modalWidth(Width::ExtraLarge)
             ->modalHeading(__('shopper::pages/settings/payments.add_payment'))
             ->modalSubmitActionLabel(__('shopper::forms.actions.save'))
@@ -88,7 +89,8 @@ class PaymentMethods extends Component implements HasActions, HasSchemas, HasTab
                         default => 'warning',
                     }),
                 ToggleColumn::make('is_enabled')
-                    ->label(__('shopper::forms.label.status')),
+                    ->label(__('shopper::forms.label.status'))
+                    ->beforeStateUpdated(fn (): mixed => $this->authorize('access_setting')),
                 TextColumn::make('updated_at')
                     ->label(__('shopper::forms.label.updated_at'))
                     ->date(),
@@ -98,12 +100,14 @@ class PaymentMethods extends Component implements HasActions, HasSchemas, HasTab
                     ->label(__('shopper::forms.actions.edit'))
                     ->icon(Untitledui::Edit03)
                     ->iconButton()
+                    ->authorize('access_setting')
                     ->modalWidth(Width::ExtraLarge)
                     ->schema($this->getPaymentFormSchema())
                     ->successNotificationTitle(__('shopper::notifications.payment.update')),
                 DeleteAction::make('delete')
                     ->label(__('shopper::forms.actions.delete'))
                     ->icon(Untitledui::Trash03)
+                    ->authorize('access_setting')
                     ->iconButton(),
             ])
             ->emptyStateIcon(Untitledui::CreditCard02)
diff --git a/packages/admin/src/Livewire/Pages/Settings/Team/Index.php b/packages/admin/src/Livewire/Pages/Settings/Team/Index.php
index 518192f4ece04b5f05eb488396e4a86fd160e7dc..b7339a7f7bce9c63bffcef6d6f3878dba1679cf0 100755
--- a/packages/admin/src/Livewire/Pages/Settings/Team/Index.php
+++ b/packages/admin/src/Livewire/Pages/Settings/Team/Index.php
@@ -38,6 +38,11 @@ class Index extends Component implements HasActions, HasSchemas, HasTable
     use InteractsWithSchemas;
     use InteractsWithTable;
 
+    public function mount(): void
+    {
+        $this->authorize('view_users');
+    }
+
     public function createRoleAction(): Action
     {
         return Action::make('createRole')
@@ -46,6 +51,7 @@ class Index extends Component implements HasActions, HasSchemas, HasTable
             ->iconButton()
             ->outlined()
             ->size(Size::Small)
+            ->authorize('access_setting')
             ->modalWidth(Width::Large)
             ->modalHeading(__('shopper::modals.roles.new'))
             ->modalDescription(__('shopper::modals.roles.new_description'))
@@ -111,6 +117,7 @@ class Index extends Component implements HasActions, HasSchemas, HasTable
                     ->icon(Untitledui::Trash03)
                     ->iconButton()
                     ->label(__('shopper::forms.actions.delete'))
+                    ->authorize('access_setting')
                     ->visible(fn (ShopperUser $record): bool => shopper()->auth()->user()->isAdmin() && ! $record->isAdmin()) // @phpstan-ignore-line
                     ->successNotificationTitle(__('shopper::notifications.users_roles.admin_deleted')),
             ]);
diff --git a/packages/admin/src/Livewire/Pages/Settings/Team/RolePermission.php b/packages/admin/src/Livewire/Pages/Settings/Team/RolePermission.php
index 778348c71f87de420151a8d9ee266baeac2f5bb3..801c117f69696af6017063938b9bfa40a75a527d 100755
--- a/packages/admin/src/Livewire/Pages/Settings/Team/RolePermission.php
+++ b/packages/admin/src/Livewire/Pages/Settings/Team/RolePermission.php
@@ -24,6 +24,7 @@ use Illuminate\Support\Facades\Blade;
 use Illuminate\Support\HtmlString;
 use Illuminate\Support\Str;
 use Livewire\Attributes\Layout;
+use Livewire\Attributes\Locked;
 use Livewire\Component;
 use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
 use Shopper\Models\Permission;
@@ -40,6 +41,7 @@ class RolePermission extends Component implements HasActions, HasSchemas
     use InteractsWithActions;
     use InteractsWithSchemas;
 
+    #[Locked]
     public Role $role;
 
     /** @var array<string, mixed>|null */
@@ -93,6 +95,7 @@ class RolePermission extends Component implements HasActions, HasSchemas
             ->label(__('shopper::pages/settings/staff.generate_permissions'))
             ->icon(Untitledui::ShieldZap)
             ->color('gray')
+            ->authorize('access_setting')
             ->modalWidth(Width::Medium)
             ->modalHeading(__('shopper::pages/settings/staff.generate_permissions'))
             ->modalDescription(__('shopper::pages/settings/staff.generate_permissions_description'))
@@ -126,8 +129,6 @@ class RolePermission extends Component implements HasActions, HasSchemas
                     ->columnSpan('full'),
             ])
             ->action(function (array $data): void {
-                $this->authorize('view_users');
-
                 $resource = $data['resource'];
                 $group = $data['group_name'] ?? null;
 
@@ -153,6 +154,7 @@ class RolePermission extends Component implements HasActions, HasSchemas
         return Action::make('createPermission')
             ->label(__('shopper::pages/settings/staff.create_permission'))
             ->icon(Untitledui::Lock04)
+            ->authorize('access_setting')
             ->modalWidth(Width::ExtraLarge)
             ->modalHeading(__('shopper::modals.permissions.new'))
             ->modalDescription(__('shopper::modals.permissions.new_description'))
@@ -180,8 +182,6 @@ class RolePermission extends Component implements HasActions, HasSchemas
                     ->columnSpan('full'),
             ])
             ->action(function (array $data): void {
-                $this->authorize('view_users');
-
                 /** @var Permission $permission */
                 $permission = Permission::query()->create($data);
 
@@ -198,7 +198,7 @@ class RolePermission extends Component implements HasActions, HasSchemas
 
     public function save(): void
     {
-        $this->authorize('view_users');
+        $this->authorize('access_setting');
 
         $this->role->update($this->form->getState());
 
diff --git a/packages/admin/src/Livewire/SlideOvers/AddProduct.php b/packages/admin/src/Livewire/SlideOvers/AddProduct.php
index 9f947034551b2b28172ba77c969acbaed9f75c08..970a63658cb60dfe8b73522b81aad9fa9df2c207 100644
--- a/packages/admin/src/Livewire/SlideOvers/AddProduct.php
+++ b/packages/admin/src/Livewire/SlideOvers/AddProduct.php
@@ -253,6 +253,7 @@ class AddProduct extends SlideOverComponent implements HasActions, HasSchemas
                                     TextInput::make('barcode')
                                         ->label(__('shopper::forms.label.barcode'))
                                         ->unique(config('shopper.models.product'), 'barcode')
+                                        ->regex('/^[A-Za-z0-9\-]*$/')
                                         ->maxLength(255),
                                     TextInput::make('quantity')
                                         ->label(__('shopper::forms.label.quantity'))
diff --git a/packages/admin/src/Livewire/SlideOvers/AddVariant.php b/packages/admin/src/Livewire/SlideOvers/AddVariant.php
index 5ea43b63ff74f53b946bc6fb3dae74d16c69760e..7eb694a5d5d8a852e459406a3ff505a8f8443e4c 100755
--- a/packages/admin/src/Livewire/SlideOvers/AddVariant.php
+++ b/packages/admin/src/Livewire/SlideOvers/AddVariant.php
@@ -182,6 +182,7 @@ class AddVariant extends SlideOverComponent implements HasActions, HasSchemas
                                         TextInput::make('barcode')
                                             ->label(__('shopper::forms.label.barcode'))
                                             ->unique(shopper_table('product_variants'), 'barcode')
+                                            ->regex('/^[A-Za-z0-9\-]*$/')
                                             ->maxLength(255),
                                         TextInput::make('quantity')
                                             ->label(__('shopper::forms.label.quantity'))
diff --git a/packages/admin/src/Livewire/SlideOvers/ChooseProductAttributes.php b/packages/admin/src/Livewire/SlideOvers/ChooseProductAttributes.php
index 8c27a66d3d8f4ff45f91751bb4163ff57145cb38..0bf4ba5f2b83499eb16812b7d6d39da085470aff 100644
--- a/packages/admin/src/Livewire/SlideOvers/ChooseProductAttributes.php
+++ b/packages/admin/src/Livewire/SlideOvers/ChooseProductAttributes.php
@@ -24,6 +24,7 @@ use Illuminate\Support\Facades\Blade;
 use Illuminate\Support\HtmlString;
 use JaOcero\RadioDeck\Forms\Components\RadioDeck;
 use Laravelcm\LivewireSlideOvers\SlideOverComponent;
+use Livewire\Attributes\Locked;
 use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
 use Shopper\Actions\Store\Product\AttachedAttributesToProductAction;
 use Shopper\Components\Separator;
@@ -47,6 +48,7 @@ class ChooseProductAttributes extends SlideOverComponent implements HasActions,
     /** @var array<string, mixed>|null */
     public ?array $data = [];
 
+    #[Locked]
     public Product $product;
 
     public static function panelMaxWidth(): string
diff --git a/packages/admin/src/Livewire/SlideOvers/CreateShippingLabel.php b/packages/admin/src/Livewire/SlideOvers/CreateShippingLabel.php
index 949dbfe5b3f43255a24c090281a039dfc5c7e881..6507a6b88c6b0823bfb6acf6139c90f2783e569e 100644
--- a/packages/admin/src/Livewire/SlideOvers/CreateShippingLabel.php
+++ b/packages/admin/src/Livewire/SlideOvers/CreateShippingLabel.php
@@ -23,6 +23,7 @@ use Illuminate\Database\Eloquent\Collection;
 use Illuminate\Support\HtmlString;
 use Laravelcm\LivewireSlideOvers\SlideOverComponent;
 use Livewire\Attributes\Computed;
+use Livewire\Attributes\Locked;
 use Shopper\Contracts\SlideOverForm;
 use Shopper\Core\Enum\FulfillmentStatus;
 use Shopper\Core\Enum\ShipmentStatus;
@@ -45,6 +46,7 @@ class CreateShippingLabel extends SlideOverComponent implements HasActions, HasS
     use InteractsWithSchemas;
     use InteractsWithSlideOverForm;
 
+    #[Locked]
     public Order $order;
 
     /** @var array<string, mixed>|null */
diff --git a/packages/admin/src/Livewire/SlideOvers/DiscountForm.php b/packages/admin/src/Livewire/SlideOvers/DiscountForm.php
index 028b62e3a707b1de520d25b347f6d412e6df293c..80db0e6e3944547ecc08712ced5c733c0fbfaca6 100755
--- a/packages/admin/src/Livewire/SlideOvers/DiscountForm.php
+++ b/packages/admin/src/Livewire/SlideOvers/DiscountForm.php
@@ -27,6 +27,7 @@ use Illuminate\Support\Facades\Blade;
 use Illuminate\Support\HtmlString;
 use Illuminate\Support\Str;
 use Laravelcm\LivewireSlideOvers\SlideOverComponent;
+use Livewire\Attributes\Locked;
 use Shopper\Actions\Store\SaveAndDispatchDiscountAction;
 use Shopper\Components\Separator;
 use Shopper\Contracts\SlideOverForm;
@@ -51,6 +52,7 @@ class DiscountForm extends SlideOverComponent implements HasActions, HasSchemas,
     use InteractsWithSchemas;
     use InteractsWithSlideOverForm;
 
+    #[Locked]
     public Discount $discount;
 
     public string $action = 'store';
diff --git a/packages/admin/src/Livewire/SlideOvers/RelatedProductsList.php b/packages/admin/src/Livewire/SlideOvers/RelatedProductsList.php
index 17b5e8d51d74df161db4a1eecb04bd78d8c73513..9d925cdf5808ef31f17c651a08e74a14afeab357 100644
--- a/packages/admin/src/Livewire/SlideOvers/RelatedProductsList.php
+++ b/packages/admin/src/Livewire/SlideOvers/RelatedProductsList.php
@@ -32,6 +32,7 @@ class RelatedProductsList extends SlideOverComponent implements HasActions, HasS
     use InteractsWithSchemas;
     use InteractsWithTable;
 
+    #[Locked]
     public Product $product;
 
     /** @var array<int> */
diff --git a/packages/admin/src/Livewire/SlideOvers/ReviewDetail.php b/packages/admin/src/Livewire/SlideOvers/ReviewDetail.php
index 8c9f31b2df0d7d34a49574926a2de322ddf3ccaf..837f010d56b50f201fcccdbe6bdf4c4616dc733a 100755
--- a/packages/admin/src/Livewire/SlideOvers/ReviewDetail.php
+++ b/packages/admin/src/Livewire/SlideOvers/ReviewDetail.php
@@ -13,6 +13,7 @@ use Filament\Schemas\Contracts\HasSchemas;
 use Filament\Support\Enums\Size;
 use Illuminate\Contracts\View\View;
 use Laravelcm\LivewireSlideOvers\SlideOverComponent;
+use Livewire\Attributes\Locked;
 use Shopper\Core\Models\Review;
 use Shopper\Traits\HandlesAuthorizationExceptions;
 
@@ -22,6 +23,7 @@ class ReviewDetail extends SlideOverComponent implements HasActions, HasSchemas
     use InteractsWithActions;
     use InteractsWithSchemas;
 
+    #[Locked]
     public Review $review;
 
     public function mount(): void
diff --git a/packages/admin/src/Livewire/SlideOvers/ShipmentAddEvent.php b/packages/admin/src/Livewire/SlideOvers/ShipmentAddEvent.php
index 20fdd06a817073213f0e3063eb6117221bc27e1b..da8c69ebeaa675c2b42d4b7e529dabb738d499e9 100644
--- a/packages/admin/src/Livewire/SlideOvers/ShipmentAddEvent.php
+++ b/packages/admin/src/Livewire/SlideOvers/ShipmentAddEvent.php
@@ -17,6 +17,7 @@ use Filament\Schemas\Concerns\InteractsWithSchemas;
 use Filament\Schemas\Contracts\HasSchemas;
 use Filament\Schemas\Schema;
 use Laravelcm\LivewireSlideOvers\SlideOverComponent;
+use Livewire\Attributes\Locked;
 use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
 use Shopper\Contracts\SlideOverForm;
 use Shopper\Core\Actions\RecordShipmentEventAction;
@@ -35,6 +36,7 @@ class ShipmentAddEvent extends SlideOverComponent implements HasActions, HasSche
     use InteractsWithSchemas;
     use InteractsWithSlideOverForm;
 
+    #[Locked]
     public OrderShipping $shipment;
 
     /** @var array<array-key, mixed>|null */
diff --git a/packages/admin/src/Livewire/SlideOvers/ShipmentDetail.php b/packages/admin/src/Livewire/SlideOvers/ShipmentDetail.php
index 37576327f71f80c7206b2f7b8bef7637c2506e0d..60adda7707dfd7c229ae90c78b0347790b56942b 100644
--- a/packages/admin/src/Livewire/SlideOvers/ShipmentDetail.php
+++ b/packages/admin/src/Livewire/SlideOvers/ShipmentDetail.php
@@ -14,6 +14,7 @@ use Illuminate\Contracts\View\View;
 use Illuminate\Database\Eloquent\Collection;
 use Laravelcm\LivewireSlideOvers\SlideOverComponent;
 use Livewire\Attributes\Computed;
+use Livewire\Attributes\Locked;
 use Livewire\Attributes\On;
 use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
 use Shopper\Core\Models\OrderShipping;
@@ -29,6 +30,7 @@ class ShipmentDetail extends SlideOverComponent implements HasActions, HasSchema
     use InteractsWithActions;
     use InteractsWithSchemas;
 
+    #[Locked]
     public OrderShipping $shipment;
 
     public static function panelMaxWidth(): string
diff --git a/packages/cart/src/Actions/CreateOrderFromCartAction.php b/packages/cart/src/Actions/CreateOrderFromCartAction.php
index e1988bfedabaeae9821baec914d6aa53ace4121f..df82e0d571ea2baba5f9dd9eb98b6d3d16096c30 100644
--- a/packages/cart/src/Actions/CreateOrderFromCartAction.php
+++ b/packages/cart/src/Actions/CreateOrderFromCartAction.php
@@ -9,9 +9,11 @@ use Illuminate\Support\Facades\DB;
 use Shopper\Cart\CartManager;
 use Shopper\Cart\Events\CartCompleted;
 use Shopper\Cart\Exceptions\CartCompletedException;
+use Shopper\Cart\Exceptions\DiscountLimitReachedException;
 use Shopper\Cart\Models\Cart;
 use Shopper\Cart\Models\CartAddress;
 use Shopper\Core\Actions\CreateOrderTaxLinesAction;
+use Shopper\Core\Models\Contracts\Order as OrderContract;
 use Shopper\Core\Models\Contracts\ProductVariant;
 use Shopper\Core\Models\Discount;
 use Shopper\Core\Models\Order;
@@ -35,12 +37,14 @@ final readonly class CreateOrderFromCartAction
                 throw new CartCompletedException;
             }
 
+            $discount = $this->reserveDiscount($cart);
+
             $context = $this->cartManager->calculate($cart);
 
             $shippingAddress = $this->createOrderAddress($cart->shippingAddress(), $cart->customer_id);
             $billingAddress = $this->createOrderAddress($cart->billingAddress(), $cart->customer_id);
 
-            $order = Order::query()->create([
+            $order = resolve(OrderContract::class)::query()->create([
                 'number' => generate_number(),
                 'price_amount' => $context->total,
                 'tax_amount' => $context->taxTotal,
@@ -50,6 +54,11 @@ final readonly class CreateOrderFromCartAction
                 'zone_id' => $cart->zone_id,
                 'shipping_address_id' => $shippingAddress?->id,
                 'billing_address_id' => $billingAddress?->id,
+                'discount_id' => $discount?->id,
+                'discount_code' => $discount?->code,
+                'discount_type' => $discount?->type->value,
+                'discount_value_at_apply' => $discount?->value,
+                'discount_currency_code' => $discount !== null ? $cart->currency_code : null,
             ]);
 
             $cart->lines->loadMorph('purchasable', [
@@ -75,16 +84,6 @@ final readonly class CreateOrderFromCartAction
 
             $order->refresh();
 
-            if ($cart->coupon_code) {
-                Discount::query()
-                    ->where('code', $cart->coupon_code)
-                    ->where(function ($query): void {
-                        $query->whereNull('usage_limit')
-                            ->orWhereColumn('total_use', '<', 'usage_limit');
-                    })
-                    ->increment('total_use');
-            }
-
             $cart->update(['completed_at' => now()]);
 
             CartCompleted::dispatch($cart, $order);
@@ -93,6 +92,49 @@ final readonly class CreateOrderFromCartAction
         });
     }
 
+    private function reserveDiscount(Cart $cart): ?Discount
+    {
+        if (! $cart->coupon_code) {
+            return null;
+        }
+
+        $discount = Discount::query()
+            ->where('code', $cart->coupon_code)
+            ->lockForUpdate()
+            ->first();
+
+        if ($discount === null) {
+            return null;
+        }
+
+        if ($discount->usage_limit_per_user && $cart->customer_id !== null) {
+            $alreadyRedeemed = resolve(OrderContract::class)::query()
+                ->where('discount_id', $discount->id)
+                ->where('customer_id', $cart->customer_id)
+                ->exists();
+
+            if ($alreadyRedeemed) {
+                throw DiscountLimitReachedException::perUser($discount->code);
+            }
+        }
+
+        $affected = Discount::query()
+            ->whereKey($discount->id)
+            ->where(function ($query): void {
+                $query->whereNull('usage_limit')
+                    ->orWhereColumn('total_use', '<', 'usage_limit');
+            })
+            ->increment('total_use');
+
+        if ($affected === 0) {
+            throw DiscountLimitReachedException::global($discount->code);
+        }
+
+        $discount->refresh();
+
+        return $discount;
+    }
+
     private function resolveItemName(Model $purchasable): string
     {
         if ($purchasable instanceof ProductVariant) {
diff --git a/packages/cart/src/Discounts/DiscountValidator.php b/packages/cart/src/Discounts/DiscountValidator.php
index 1c899fa858e0723264d1f6309f53124f4b86dc11..f86c563fe4e9d37e133c87ec394b0730311cd2ba 100644
--- a/packages/cart/src/Discounts/DiscountValidator.php
+++ b/packages/cart/src/Discounts/DiscountValidator.php
@@ -8,6 +8,7 @@ use Shopper\Cart\Pipelines\CartPipelineContext;
 use Shopper\Core\Enum\DiscountCondition;
 use Shopper\Core\Enum\DiscountEligibility;
 use Shopper\Core\Enum\DiscountRequirement;
+use Shopper\Core\Models\Contracts\Order as OrderContract;
 use Shopper\Core\Models\Discount;
 
 final readonly class DiscountValidator
@@ -31,13 +32,12 @@ final readonly class DiscountValidator
         }
 
         if ($discount->usage_limit_per_user && $context->cart->customer_id) {
-            $userUses = $discount->items()
-                ->where('condition', DiscountCondition::Eligibility)
-                ->where('discountable_type', config('auth.providers.users.model'))
-                ->where('discountable_id', $context->cart->customer_id)
-                ->value('total_use') ?? 0;
+            $alreadyRedeemed = resolve(OrderContract::class)::query()
+                ->where('discount_id', $discount->id)
+                ->where('customer_id', $context->cart->customer_id)
+                ->exists();
 
-            if ($userUses > 0) {
+            if ($alreadyRedeemed) {
                 return new DiscountValidationResult(false, __('shopper-cart::messages.discount.already_used'));
             }
         }
diff --git a/packages/cart/src/Exceptions/DiscountLimitReachedException.php b/packages/cart/src/Exceptions/DiscountLimitReachedException.php
new file mode 100644
index 0000000000000000000000000000000000000000..382ed5b805340096ad2655afb2c4c1dc1d735ea8
--- /dev/null
+++ b/packages/cart/src/Exceptions/DiscountLimitReachedException.php
@@ -0,0 +1,26 @@
+<?php
+
+declare(strict_types=1);
+
+namespace Shopper\Cart\Exceptions;
+
+use RuntimeException;
+
+final class DiscountLimitReachedException extends RuntimeException
+{
+    public static function global(string $code): self
+    {
+        return new self(
+            "The discount [{$code}] reached its global usage limit between cart validation and order commit. "
+            .'No order was created.'
+        );
+    }
+
+    public static function perUser(string $code): self
+    {
+        return new self(
+            "The discount [{$code}] has already been redeemed by this customer and is limited to one use per customer. "
+            .'No order was created.'
+        );
+    }
+}
diff --git a/packages/core/database/migrations/2026_05_06_000001_add_discount_columns_to_orders_table.php b/packages/core/database/migrations/2026_05_06_000001_add_discount_columns_to_orders_table.php
new file mode 100644
index 0000000000000000000000000000000000000000..7f664ddb1c2b8cd824b4cf2ef701a9556e88dc95
--- /dev/null
+++ b/packages/core/database/migrations/2026_05_06_000001_add_discount_columns_to_orders_table.php
@@ -0,0 +1,38 @@
+<?php
+
+declare(strict_types=1);
+
+use Illuminate\Database\Schema\Blueprint;
+use Illuminate\Support\Facades\Schema;
+use Shopper\Core\Helpers\Migration;
+
+return new class extends Migration
+{
+    public function up(): void
+    {
+        Schema::table($this->getTableName('orders'), function (Blueprint $table): void {
+            $this->addForeignKey($table, 'discount_id', $this->getTableName('discounts'));
+
+            $table->after('discount_id', static function (Blueprint $table): void {
+                $table->string('discount_code')->nullable();
+                $table->string('discount_type', 32)->nullable();
+                $table->unsignedInteger('discount_value_at_apply')->nullable();
+                $table->char('discount_currency_code', 3)->nullable();
+            });
+        });
+    }
+
+    public function down(): void
+    {
+        Schema::table($this->getTableName('orders'), function (Blueprint $table): void {
+            $this->removeForeignKeyAndColumn($table, 'discount_id');
+
+            $table->dropColumn([
+                'discount_code',
+                'discount_type',
+                'discount_value_at_apply',
+                'discount_currency_code',
+            ]);
+        });
+    }
+};

# (19 test/doc file(s) of the upstream fix omitted here)

Pre-Patch Source Files (Vulnerable state of files modified by patch)
### packages/admin/src/Livewire/Components/Customers/Addresses.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Customers;

use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Collection;
use Illuminate\Database\Eloquent\Model;
use Livewire\Attributes\Computed;
use Livewire\Component;
use Shopper\Core\Models\Address;
use Shopper\Core\Models\Contracts\Address as AddressContract;
use Shopper\Models\Contracts\ShopperUser;
use Shopper\Traits\HandlesAuthorizationExceptions;

class Addresses extends Component
{
    use HandlesAuthorizationExceptions;

    /** @var Model&ShopperUser */
    public ShopperUser $customer;

    /**
     * @return Collection<int, Address>
     */
    #[Computed]
    public function addresses(): Collection
    {
        return resolve(AddressContract::class)::with('country')
            ->whereBelongsTo($this->customer)
            ->get();
    }

    public function render(): View
    {
        return view('shopper::livewire.components.customers.addresses');
    }
}

```

### packages/admin/src/Livewire/Components/Customers/Orders.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Customers;

use Filament\Actions\Action;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Columns\ViewColumn;
use Filament\Tables\Concerns\InteractsWithTable;
use Filament\Tables\Contracts\HasTable;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Table;
use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Model;
use Livewire\Component;
use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
use Shopper\Core\Models\Contracts\Order;
use Shopper\Models\Contracts\ShopperUser;
use Shopper\Traits\HandlesAuthorizationExceptions;

class Orders extends Component implements HasActions, HasSchemas, HasTable
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;
    use InteractsWithTable;

    /** @var Model&ShopperUser */
    public ShopperUser $customer;

    public function table(Table $table): Table
    {
        return $table
            ->query(
                resolve(Order::class)::query()
                    ->with([
                        'items',
                        'items.product',
                        'items.product.media',
                        'zone',
                        'channel',
                    ])
                    ->whereBelongsTo($this->customer, 'customer')
                    ->latest()
            )
            ->columns([
                TextColumn::make('number')
                    ->label('#')
                    ->searchable()
                    ->extraAttributes(['class' => 'uppercase'])
                    ->sortable(),
                TextColumn::make('created_at')
                    ->label(__('shopper::words.date'))
                    ->date()
                    ->sortable(),
                ViewColumn::make('status')
                    ->label(__('shopper::forms.label.status'))
                    ->view('shopper::livewire.tables.cells.orders.status')
                    ->extraCellAttributes(['class' => 'whitespace-nowrap']),
                TextColumn::make('total')
                    ->label(__('shopper::forms.label.price_amount'))
                    ->state(fn (Order $record): string => shopper_money_format(
                        amount: $record->total(),
                        currency: $record->currency_code
                    )),
                TextColumn::make('id')
                    ->label(__('shopper::words.purchased'))
                    ->formatStateUsing(fn (Order $record): View => view(
                        'shopper::livewire.tables.cells.orders.purchased',
                        ['order' => $record]
                    )),
                TextColumn::make('zone.name')
                    ->label(__('shopper::pages/settings/zones.single'))
                    ->searchable()
                    ->sortable()
                    ->toggleable()
                    ->toggledHiddenByDefault(),
                TextColumn::make('channel.name')
                    ->label(__('shopper::pages/settings/channels.single'))
                    ->searchable()
                    ->sortable()
                    ->toggleable()
                    ->toggledHiddenByDefault(),
            ])
            ->filters([
                SelectFilter::make('status')
                    ->label(__('shopper::forms.label.status'))
                    ->options(\Shopper\Core\Enum\OrderStatus::class)
                    ->multiple(),
                SelectFilter::make('payment_status')
                    ->label(__('shopper::forms.label.payment_status'))
                    ->options(\Shopper\Core\Enum\PaymentStatus::class)
                    ->multiple(),
                SelectFilter::make('zone_id')
                    ->label(__('shopper::pages/settings/zones.single'))
                    ->relationship('zone', 'name')
                    ->searchable()
                    ->preload(),
                SelectFilter::make('channel_id')
                    ->label(__('shopper::pages/settings/channels.single'))
                    ->relationship('channel', 'name')
                    ->searchable()
                    ->preload(),
            ])
            ->recordActions([
                Action::make('view')
                    ->label(__('shopper::words.details'))
                    ->icon(Untitledui::Eye)
                    ->iconButton()
                    ->action(fn (Order $record) => $this->redirectRoute(
                        name: 'shopper.orders.detail',
                        parameters: ['order' => $record],
                        navigate: true
                    )),
            ])
            ->emptyState(view('shopper::livewire.tables.empty-states.orders'));
    }

    public function render(): View
    {
        return view('shopper::livewire.components.customers.orders');
    }
}

```

### packages/admin/src/Livewire/Components/Customers/Profile.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Customers;

use Illuminate\Contracts\View\View;
use Livewire\Component;
use Shopper\Models\Contracts\ShopperUser;
use Shopper\Traits\HandlesAuthorizationExceptions;

class Profile extends Component
{
    use HandlesAuthorizationExceptions;

    public ShopperUser $customer;

    public function render(): View
    {
        return view('shopper::livewire.components.customers.profile');
    }
}

```

### packages/admin/src/Livewire/Components/Orders/Fulfillment.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Orders;

use BackedEnum;
use Illuminate\Contracts\View\View;
use Livewire\Attributes\On;
use Livewire\Component;
use Shopper\Core\Enum\OrderStatus;
use Shopper\Core\Enum\ShippingStatus;
use Shopper\Core\Models\Contracts\Order;
use Shopper\Core\Models\Country;
use Shopper\Traits\HandlesAuthorizationExceptions;

class Fulfillment extends Component
{
    use HandlesAuthorizationExceptions;

    public Order $order;

    public function hasUnfulfilledItems(): bool
    {
        return $this->order->items()
            ->whereNull('order_shipping_id')
            ->exists();
    }

    public function openShippingLabel(): void
    {
        $this->dispatch(
            'openPanel',
            component: 'shopper-slide-overs.create-shipping-label',
            arguments: ['order' => $this->order->id],
        );
    }

    #[On('order.updated')]
    #[On('order.shipping.created')]
    public function render(): View
    {
        $this->order->loadMissing('shippingAddress');

        $shippingAddress = $this->order->shippingAddress;

        $country = $shippingAddress
            ? Country::query()->where('name', $shippingAddress->country_name)->first()
            : null;

        return view('shopper::livewire.components.orders.fulfillment', [
            'shippingAddress' => $shippingAddress,
            'country' => $country,
            'currentStep' => $this->resolveCurrentStep(),
            'steps' => $this->steps(),
        ]);
    }

    /**
     * @return array<int, array{label: string, icon: string|BackedEnum}>
     */
    private function steps(): array
    {
        return [
            ['label' => OrderStatus::New->getLabel(), 'icon' => OrderStatus::New->getIcon()],
            ['label' => OrderStatus::Processing->getLabel(), 'icon' => OrderStatus::Processing->getIcon()],
            ['label' => ShippingStatus::Shipped->getLabel(), 'icon' => ShippingStatus::Shipped->getIcon()],
            ['label' => OrderStatus::Completed->getLabel(), 'icon' => OrderStatus::Completed->getIcon()],
        ];
    }

    private function resolveCurrentStep(): int
    {
        if ($this->order->status === OrderStatus::Cancelled || $this->order->status === OrderStatus::Archived) {
            return 0;
        }

        return match (true) {
            $this->order->isCompleted() => 4,
            $this->order->shipping_status !== ShippingStatus::Unfulfilled => 3,
            $this->order->isProcessing() => 2,
            default => 1,
        };
    }
}

```

### packages/admin/src/Livewire/Components/Orders/OrderCustomer.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Orders;

use Illuminate\Contracts\View\View;
use Livewire\Attributes\Computed;
use Livewire\Component;
use Shopper\Core\Models\Contracts\Order;
use Shopper\Models\Contracts\ShopperUser;
use Shopper\Traits\HandlesAuthorizationExceptions;

/**
 * @property-read ShopperUser|null $customer
 */
class OrderCustomer extends Component
{
    use HandlesAuthorizationExceptions;

    public Order $order;

    #[Computed]
    public function customer(): ?ShopperUser
    {
        $userModel = config('auth.providers.users.model');

        return $userModel::query()
            ->withCount('orders')
            ->find($this->order->customer_id);
    }

    public function render(): View
    {
        $this->order->loadMissing(['shippingAddress', 'billingAddress']);

        return view('shopper::livewire.components.orders.order-customer', [
            'shippingAddress' => $this->order->shippingAddress,
            'billingAddress' => $this->order->billingAddress,
        ]);
    }
}

```

### packages/admin/src/Livewire/Components/Orders/OrderItems.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Orders;

use Illuminate\Contracts\View\View;
use Livewire\Attributes\On;
use Livewire\Component;
use Livewire\WithPagination;
use Shopper\Core\Models\Contracts\Order;
use Shopper\Traits\HandlesAuthorizationExceptions;

class OrderItems extends Component
{
    use HandlesAuthorizationExceptions;
    use WithPagination;

    public Order $order;

    public int $perPage = 3;

    #[On('order.updated')]
    #[On('order.shipping.created')]
    public function render(): View
    {
        return view('shopper::livewire.components.orders.order-items', [
            'items' => $this->order
                ->items()
                ->with('product', 'product.media', 'product.prices')
                ->simplePaginate($this->perPage),
        ]);
    }
}

```

### packages/admin/src/Livewire/Components/Orders/OrderNotes.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Orders;

use Filament\Notifications\Notification;
use Illuminate\Contracts\View\View;
use Livewire\Attributes\Validate;
use Livewire\Component;
use Shopper\Core\Events\Orders\OrderNoteAdded;
use Shopper\Core\Models\Contracts\Order;
use Shopper\Traits\HandlesAuthorizationExceptions;

class OrderNotes extends Component
{
    use HandlesAuthorizationExceptions;

    public Order $order;

    #[Validate('required|string')]
    public ?string $notes = null;

    public function leaveNotes(): void
    {
        $this->validate();

        $this->order->update(['notes' => $this->notes]);

        event(new OrderNoteAdded($this->order));

        Notification::make()
            ->title(__('shopper::pages/orders.notifications.note_added'))
            ->success()
            ->send();
    }

    public function render(): View
    {
        return view('shopper::livewire.components.orders.order-notes');
    }
}

```

### packages/admin/src/Livewire/Components/Orders/OrderSummary.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Orders;

use Illuminate\Contracts\View\View;
use Livewire\Attributes\On;
use Livewire\Component;
use Shopper\Core\Models\Contracts\Order;
use Shopper\Core\Models\Contracts\TaxZone;
use Shopper\Traits\HandlesAuthorizationExceptions;

class OrderSummary extends Component
{
    use HandlesAuthorizationExceptions;

    public Order $order;

    #[On('order.updated')]
    public function render(): View
    {
        $this->order->loadMissing(['shippingOption.carrier', 'paymentMethod', 'items', 'zone.countries']);

        $shippingOption = $this->order->shippingOption;
        $carrier = $shippingOption?->carrier;
        $paymentMethod = $this->order->paymentMethod;
        $subtotal = $this->order->total();
        $shippingPrice = $shippingOption?->price ?? 0; // @phpstan-ignore nullsafe.neverNull
        $taxAmount = $this->order->tax_amount ?? 0;
        $isTaxInclusive = $this->resolveTaxInclusivity();

        return view('shopper::livewire.components.orders.order-summary', [
            'subtotal' => $subtotal,
            'shippingPrice' => $shippingPrice,
            'shippingOption' => $shippingOption,
            'taxAmount' => $taxAmount,
            'isTaxInclusive' => $isTaxInclusive,
            'carrierLogoUrl' => $carrier?->logo(),
            'paymentLogoUrl' => $paymentMethod?->logo(),
            'itemsCount' => $this->order->items->count(),
            'total' => $this->order->price_amount !== null
                ? $this->order->price_amount
                : ($subtotal + $shippingPrice + ($isTaxInclusive ? 0 : $taxAmount)),
        ]);
    }

    private function resolveTaxInclusivity(): bool
    {
        $zone = $this->order->zone;

        if (! $zone) {
            return false;
        }

        $country = $zone->countries()->first();

        if (! $country) {
            return false;
        }

        $taxZone = resolve(TaxZone::class)::query()
            ->where('country_id', $country->id)
            ->first();

        if (! $taxZone) {
            return false;
        }

        return $taxZone->is_tax_inclusive;
    }
}

```

### packages/admin/src/Livewire/Components/Products/Form/Attributes.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Products\Form;

use Filament\Actions\Action;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Columns\ViewColumn;
use Filament\Tables\Concerns\InteractsWithTable;
use Filament\Tables\Contracts\HasTable;
use Filament\Tables\Grouping\Group;
use Filament\Tables\Table;
use Illuminate\Contracts\View\View;
use Livewire\Attributes\Lazy;
use Livewire\Component;
use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
use Shopper\Actions\Store\Product\DetachAttributesToProductAction;
use Shopper\Components\Tables\IconColumn;
use Shopper\Core\Models\Attribute;
use Shopper\Core\Models\AttributeProduct;
use Shopper\Core\Models\Contracts\Product;
use Shopper\Traits\HandlesAuthorizationExceptions;

#[Lazy]
class Attributes extends Component implements HasActions, HasSchemas, HasTable
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;
    use InteractsWithTable;

    public Product $product;

    public function placeholder(): View
    {
        return view('shopper::components.skeleton.products.section');
    }

    public function table(Table $table): Table
    {
        return $table
            ->heading(__('shopper::pages/attributes.menu'))
            ->description(__('shopper::pages/attributes.description'))
            ->query(
                AttributeProduct::with(['attribute', 'value', 'value.attribute'])
                    ->where('product_id', $this->product->id)
            )
            ->columns([
                IconColumn::make('attribute.icon')
                    ->label(__('shopper::forms.label.icon')),
                TextColumn::make('attribute.name')
                    ->label(__('shopper::forms.label.name')),
                ViewColumn::make('attribute_value_id')
                    ->label(__('shopper::forms.label.value'))
                    ->view('shopper::livewire.tables.cells.products.attribute-value'),
                TextColumn::make('attribute_custom_value')
                    ->label(__('shopper::forms.label.attribute_custom_value'))
                    ->html()
                    ->limit(150),
            ])
            ->groups([
                Group::make('attribute_id')
                    ->label(__('shopper::forms.label.attribute'))
                    ->getTitleFromRecordUsing(fn (AttributeProduct $record): string => $record->attribute->name),
            ])
            ->defaultGroup('attribute_id')
            ->headerActions([
                Action::make('choose')
                    ->label(__('shopper::pages/products.attributes.choose'))
                    ->action(
                        fn () => $this->dispatch(
                            'openPanel',
                            component: 'shopper-slide-overs.choose-product-attributes',
                            arguments: ['product' => $this->product]
                        )
                    )
                    ->visible(Attribute::query()->count() > 0),
            ])
            ->recordActions([
                Action::make('delete')
                    ->label(__('shopper::forms.actions.delete'))
                    ->icon(Untitledui::Trash03)
                    ->iconButton()
                    ->color('danger')
                    ->requiresConfirmation()
                    ->action(function (AttributeProduct $record): void {
                        $this->authorize('delete_attributes', $record);

                        app()->call(DetachAttributesToProductAction::class, [
                            'attributeProduct' => $record,
                            'product' => $this->product,
                        ]);

                        $this->dispatch('product.updated');
                    })
                    ->successNotificationTitle(__('shopper::pages/products.attributes.session.delete_message')),
            ])
            ->emptyStateHeading(__('shopper::pages/products.attributes.empty_title'))
            ->emptyStateDescription(__('shopper::pages/products.attributes.empty_values'))
            ->emptyStateIcon(Untitledui::PuzzlePiece);
    }

    public function render(): View
    {
        return view('shopper::livewire.components.products.forms.attributes');
    }
}

```

### packages/admin/src/Livewire/Components/Products/Form/Edit.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Products\Form;

use CodeWithDennis\FilamentSelectTree\SelectTree;
use Filament\Actions\Action;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Forms\Components\DateTimePicker;
use Filament\Forms\Components\RichEditor;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\Toggle;
use Filament\Notifications\Notification;
use Filament\Schemas\Components\Grid;
use Filament\Schemas\Components\Group;
use Filament\Schemas\Components\Section;
use Filament\Schemas\Components\Utilities\Set;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Schemas\Schema;
use Filament\Support\Enums\IconSize;
use Filament\Support\Enums\Width;
use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Str;
use Livewire\Component;
use Shopper\Actions\Store\Product\UpdateProductAction;
use Shopper\Components\Separator;
use Shopper\Core\Models\Contracts\Product;
use Shopper\Core\Models\ProductTag;
use Shopper\Feature;
use Shopper\Traits\HandlesAuthorizationExceptions;

/**
 * @property-read Schema $form
 */
class Edit extends Component implements HasActions, HasSchemas
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;

    public Model&Product $product;

    /**
     * @var array<string, mixed>|null
     */
    public ?array $data = [];

    public function mount(): void
    {
        $this->form->fill($this->product->toArray());
    }

    public function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                Grid::make()
                    ->schema([
                        Section::make(__('shopper::pages/products.general'))
                            ->description($this->product->type?->getDescription())
                            ->icon($this->product->type?->getIcon())
                            ->iconSize(IconSize::Large)
                            ->schema([
                                TextInput::make('name')
                                    ->label(__('shopper::forms.label.name'))
                                    ->required()
                                    ->maxLength(255)
                                    ->live(onBlur: true)
                                    ->afterStateUpdated(function (?string $state, Set $set): void {
                                        if ($state) {
                                            $set('slug', Str::slug($state));
                                        }
                                    }),
                                TextInput::make('slug')
                                    ->label(__('shopper::forms.label.slug'))
                                    ->disabled()
                                    ->dehydrated()
                                    ->required()
                                    ->maxLength(255)
                                    ->unique(config('shopper.models.product'), 'slug', ignoreRecord: true),
                                Textarea::make('summary')
                                    ->label(__('shopper::forms.label.summary'))
                                    ->columnSpan('full'),
                                Toggle::make('featured')
                                    ->label(__('shopper::forms.label.featured'))
                                    ->helperText(__('shopper::pages/products.featured_help_text'))
                                    ->onColor('success')
                                    ->default(true),
                                RichEditor::make('description')
                                    ->label(__('shopper::forms.label.description'))
                                    ->columnSpan('full'),
                                Group::make()
                                    ->schema([
                                        Separator::make()->columnSpanFull(),
                                        TextInput::make('external_id')
                                            ->label(__('shopper::forms.label.external_id'))
                                            ->required()
                                            ->unique(config('shopper.models.product'), 'external_id', ignoreRecord: true)
                                            ->helperText(__('shopper::pages/products.external_id_description')),
                                        Select::make('supplier_id')
                                            ->label(__('shopper::forms.label.supplier'))
                                            ->required()
                                            ->relationship('supplier', 'name', fn (Builder $query) => $query->where('is_enabled', true))
                                            ->searchable()
                                            ->preload()
                                            ->visible(Feature::enabled('supplier')),
                                    ])
                                    ->columnSpanFull()
                                    ->columns()
                                    ->visible($this->product->isExternal()),
                            ])
                            ->columns()
                            ->columnSpanFull(),
                    ])
                    ->columnSpanFull()
                    ->columnSpan(['lg' => 2]),
                Group::make()
                    ->schema([
                        Section::make(__('shopper::pages/products.status'))
                            ->schema([
                                Toggle::make('is_visible')
                                    ->label(__('shopper::forms.label.visible'))
                                    ->helperText(__('shopper::pages/products.visible_help_text'))
                                    ->onColor('success')
                                    ->default(true),
                                DateTimePicker::make('published_at')
                                    ->label(__('shopper::forms.label.availability'))
                                    ->native(false)
                                    ->helperText(__('shopper::pages/products.availability_description'))
                                    ->required(),
                            ]),
                        Section::make(__('shopper::pages/products.product_associations'))
                            ->schema([
                                Select::make('brand_id')
                                    ->label(__('shopper::forms.label.brand'))
                                    ->relationship('brand', 'name', fn (Builder $query) => $query->where('is_enabled', true))
                                    ->searchable()
                                    ->preload()
                                    ->visible(Feature::enabled('brand')),
                                SelectTree::make('categories')
                                    ->label(__('shopper::pages/categories.menu'))
                                    ->enableBranchNode()
                                    ->relationship(
                                        relationship: 'categories',
                                        titleAttribute: 'name',
                                        parentAttribute: 'parent_id',
                                        modifyQueryUsing: fn (Builder $query) => $query->where('is_enabled', true)
                                    )
                                    ->searchable()
                                    ->visible(Feature::enabled('category'))
                                    ->withCount(),
                                Select::make('channels')
                                    ->label(__('shopper::pages/settings/menu.sales'))
                                    ->relationship(
                                        name: 'channels',
                                        titleAttribute: 'name',
                                        modifyQueryUsing: fn (Builder $query) => $query->where('is_enabled', true)
                                    )
                                    ->searchable()
                                    ->preload()
                                    ->multiple(),
                                Select::make('collections')
                                    ->label(__('shopper::pages/collections.menu'))
                                    ->relationship('collections', 'name')
                                    ->searchable()
                                    ->preload()
                                    ->multiple()
                                    ->visible(Feature::enabled('collection')),
                                Select::make('tags')
                                    ->label(__('shopper::pages/tags.menu'))
                                    ->relationship('tags', 'name')
                                    ->searchable()
                                    ->preload()
                                    ->multiple()
                                    ->createOptionForm([
                                        TextInput::make('name')
                                            ->label(__('shopper::forms.label.name'))
                                            ->required()
                                            ->live(onBlur: true)
                                            ->afterStateUpdated(fn (?string $state, Set $set): mixed => $set('slug', Str::slug($state ?? ''))),
                                        TextInput::make('slug')
                                            ->label(__('shopper::forms.label.slug'))
                                            ->disabled()
                                            ->dehydrated()
                                            ->required()
                                            ->unique(ProductTag::class, 'slug'),
                                    ])
                                    ->createOptionModalHeading(__('shopper::pages/tags.create'))
                                    ->createOptionAction(fn (Action $action): Action => $action->modalWidth(Width::Medium))
                                    ->visible(Feature::enabled('tag')),
                            ])
                            ->visible(
                                Feature::enabled('brand')
                                || Feature::enabled('category')
                                || Feature::enabled('collection')
                                || Feature::enabled('tag')
                            ),
                    ])
                    ->columnSpan(['lg' => 1]),
            ])
            ->columns(3)
            ->statePath('data')
            ->model($this->product);
    }

    public function store(): void
    {
        $this->validate();

        $this->product = app()->call(UpdateProductAction::class, [
            'values' => $this->form->getState(),
            'product' => $this->product,
        ]);

        $this->form->model($this->product)->saveRelationships();

        $this->dispatch('product.updated');

        Notification::make()
            ->title(__('shopper::notifications.update', ['item' => __('shopper::pages/products.single')]))
            ->success()
            ->send();
    }

    public function render(): View
    {
        return view('shopper::livewire.components.products.forms.edit');
    }
}

```

### packages/admin/src/Livewire/Components/Products/Form/Files.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Products\Form;

use Filament\Forms\Components\SpatieMediaLibraryFileUpload;
use Filament\Notifications\Notification;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Schemas\Schema;
use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Model;
use Livewire\Component;
use Shopper\Core\Models\Contracts\Product;
use Shopper\Traits\HandlesAuthorizationExceptions;

/**
 * @property-read Schema $form
 */
class Files extends Component implements HasSchemas
{
    use HandlesAuthorizationExceptions;
    use InteractsWithSchemas;

    /** @var Model&Product */
    public Product $product;

    /** @var array<string, mixed>|null */
    public ?array $data = [];

    public function mount(): void
    {
        $this->form->fill($this->product->toArray());
    }

    public function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                SpatieMediaLibraryFileUpload::make('files')
                    ->collection('files')
                    ->label(__('shopper::words.files'))
                    ->helperText(__('shopper::pages/products.files_helpText'))
                    ->multiple()
                    ->panelLayout('grid')
                    ->columnSpan(['lg' => 2]),
            ])
            ->columns(3)
            ->statePath('data')
            ->model($this->product);
    }

    public function store(): void
    {
        $this->product->update($this->form->getState());

        $this->dispatch('product.updated');

        Notification::make()
            ->body(__('shopper::pages/products.notifications.files_update'))
            ->success()
            ->send();
    }

    public function render(): View
    {
        return view('shopper::livewire.components.products.forms.files');
    }
}

```

### packages/admin/src/Livewire/Components/Products/Form/Inventory.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Products\Form;

use Filament\Actions\Action;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\TextInput;
use Filament\Notifications\Notification;
use Filament\Schemas\Components\Grid;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Schemas\Schema;
use Filament\Support\Enums\Width;
use Filament\Tables\Columns\Summarizers\Sum;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Concerns\InteractsWithTable;
use Filament\Tables\Contracts\HasTable;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Grouping\Group;
use Filament\Tables\Table;
use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Model;
use Livewire\Attributes\On;
use Livewire\Component;
use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
use Shopper\Components\Section;
use Shopper\Core\Models\Contracts\Product;
use Shopper\Core\Models\InventoryHistory;
use Shopper\Traits\HandlesAuthorizationExceptions;

/**
 * @property-read Schema $form
 */
class Inventory extends Component implements HasActions, HasSchemas, HasTable
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;
    use InteractsWithTable;

    /** @var Model&Product */
    public Product $product;

    /** @var array<string, mixed>|null */
    public ?array $data = [];

    public function mount(): void
    {
        $this->form->fill($this->product->toArray());
    }

    public function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                Section::make(__('shopper::pages/products.inventory.title'))
                    ->aside()
                    ->compact()
                    ->description(__('shopper::pages/products.inventory.description'))
                    ->extraAttributes(['class' => 'sh-section-aside'])
                    ->schema([
                        Grid::make()
                            ->schema([
                                TextInput::make('sku')
                                    ->label(__('shopper::forms.label.sku'))
                                    ->unique(config('shopper.models.product'), 'sku', ignoreRecord: true)
                                    ->maxLength(255),
                                TextInput::make('barcode')
                                    ->label(__('shopper::forms.label.barcode'))
                                    ->unique(config('shopper.models.product'), 'barcode', ignoreRecord: true)
                                    ->maxLength(255),
                                TextInput::make('security_stock')
                                    ->label(__('shopper::forms.label.safety_stock'))
                                    ->helperText(__('shopper::pages/products.safety_security_help_text'))
                                    ->numeric()
                                    ->default(0)
                                    ->rules(['integer', 'min:0']),
                            ]),
                    ]),
            ])
            ->statePath('data')
            ->model($this->product);
    }

    public function table(Table $table): Table
    {
        return $table
            ->query(
                InventoryHistory::with(['inventory', 'stockable'])
                    ->where('stockable_id', $this->product->id)
                    ->where('stockable_type', 'product')
                    ->latest()
            )
            ->columns([
                TextColumn::make('created_at')
                    ->label(__('shopper::words.date'))
                    ->since()
                    ->sortable(),
                TextColumn::make('event')
                    ->label(__('shopper::words.event')),
                TextColumn::make('inventory.name')
                    ->label(__('shopper::pages/settings/menu.location')),
                TextColumn::make('adjustment')
                    ->label(__('shopper::words.adjustment'))
                    ->color(function (InventoryHistory $record): string {
                        if ($record->old_quantity <= 0) {
                            return 'danger';
                        }

                        return 'success';
                    })
                    ->alignRight(),
                TextColumn::make('quantity')
                    ->label(__('shopper::pages/products.inventory.movement'))
                    ->color(fn (InventoryHistory $record): string => $record->quantity <= 0 ? 'danger' : 'gray')
                    ->alignRight()
                    ->summarize([
                        Sum::make()
                            ->label(__('shopper::words.total'))
                            ->numeric(),
                    ]),
            ])
            ->headerActions([
                Action::make('stock')
                    ->label(__('shopper::forms.label.add_stock'))
                    ->icon(Untitledui::Package)
                    ->color('gray')
                    ->modalWidth(Width::Large)
                    ->schema([
                        Select::make('inventory')
                            ->label(__('shopper::pages/products.inventory_name'))
                            ->relationship('inventory', 'name')
                            ->native(false)
                            ->required(),
                        TextInput::make('quantity')
                            ->label(__('shopper::forms.label.quantity'))
                            ->placeholder('-10 or -5 or 50, etc')
                            ->numeric()
                            ->required(),
                    ])
                    ->action(function (array $data): void {
                        $inventoryId = (int) $data['inventory'];
                        $quantity = (int) $data['quantity'];
                        $currentStock = InventoryHistory::query()
                            ->where('inventory_id', $inventoryId)
                            ->where('stockable_id', $this->product->id)
                            ->where('stockable_type', 'product')
                            ->get()
                            ->sum('quantity');

                        $realTimeStock = $currentStock + $quantity;

                        if ($realTimeStock >= $currentStock) {
                            $this->product->mutateStock(
                                inventoryId: $inventoryId,
                                quantity: $quantity,
                                oldQuantity: $quantity,
                                event: __('shopper::pages/products.inventory.add'),
                            );
                        } else {
                            $this->product->decreaseStock(
                                inventoryId: $inventoryId,
                                quantity: $quantity,
                                oldQuantity: $quantity,
                                event: __('shopper::pages/products.inventory.remove'),
                            );
                        }

                        Notification::make()
                            ->title(__('Stock successfully Updated'))
                            ->success()
                            ->send();

                        $this->dispatch('inventory.updated');
                    }),
            ])
            ->filters([
                SelectFilter::make('inventory')
                    ->relationship('inventory', 'name')
                    ->searchable(),
            ])
            ->groups([
                Group::make('inventory.name')
                    ->label(__('shopper::pages/settings/menu.location'))
                    ->collapsible(),
            ])
            ->emptyStateIcon(Untitledui::File05)
            ->emptyStateDescription(__('shopper::pages/products.inventory.empty'));
    }

    public function store(): void
    {
        $this->product->update($this->form->getState());

        $this->dispatch('product.updated');

        Notification::make()
            ->title(__('shopper::pages/products.notifications.stock_update'))
            ->success()
            ->send();
    }

    #[On('inventory.updated')]
    public function render(): View
    {
        return view('shopper::livewire.components.products.forms.inventory');
    }
}

```

### packages/admin/src/Livewire/Components/Products/Form/Media.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Products\Form;

use Filament\Forms\Components\SpatieMediaLibraryFileUpload;
use Filament\Notifications\Notification;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Schemas\Schema;
use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Model;
use Livewire\Component;
use Shopper\Core\Models\Contracts\Product;
use Shopper\Traits\HandlesAuthorizationExceptions;

/**
 * @property-read Schema $form
 */
class Media extends Component implements HasSchemas
{
    use HandlesAuthorizationExceptions;
    use InteractsWithSchemas;

    /** @var Model&Product */
    public Product $product;

    /** @var array<string, mixed>|null */
    public ?array $data = [];

    public function mount(): void
    {
        $this->form->fill($this->product->toArray());
    }

    public function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                SpatieMediaLibraryFileUpload::make('thumbnail')
                    ->collection(config('shopper.media.storage.thumbnail_collection'))
                    ->label(__('shopper::forms.label.thumbnail'))
                    ->helperText(__('shopper::pages/products.thumbnail_helpText'))
                    ->image()
                    ->maxSize(config('shopper.media.max_size.thumbnail'))
                    ->columnSpan(['lg' => 1]),
                SpatieMediaLibraryFileUpload::make('images')
                    ->collection(config('shopper.media.storage.collection_name'))
                    ->label(__('shopper::words.images'))
                    ->helperText(__('shopper::pages/products.images_helpText'))
                    ->multiple()
                    ->panelLayout('grid')
                    ->maxSize(config('shopper.media.max_size.images'))
                    ->columnSpan(['lg' => 2]),
            ])
            ->columns(3)
            ->statePath('data')
            ->model($this->product);
    }

    public function store(): void
    {
        $this->validate();

        $this->product->update($this->form->getState());

        $this->dispatch('product.updated');

        Notification::make()
            ->body(__('shopper::pages/products.notifications.media_update'))
            ->success()
            ->send();
    }

    public function render(): View
    {
        return view('shopper::livewire.components.products.forms.media');
    }
}

```

### packages/admin/src/Livewire/Components/Products/Form/RelatedProducts.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Products\Form;

use Filament\Actions\Action;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Notifications\Notification;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Model;
use Livewire\Attributes\Computed;
use Livewire\Attributes\Lazy;
use Livewire\Component;
use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
use Shopper\Core\Models\Contracts\Product;
use Shopper\Traits\HandlesAuthorizationExceptions;

#[Lazy]
class RelatedProducts extends Component implements HasActions, HasSchemas
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;

    /** @var Model&Product */
    public Product $product;

    public function mount(): void
    {
        $this->product->load('relatedProducts');
    }

    public function placeholder(): View
    {
        return view('shopper::components.skeleton.products.section');
    }

    public function removeAction(): Action
    {
        return Action::make('remove')
            ->label(__('shopper::forms.actions.remove'))
            ->icon(Untitledui::Trash03)
            ->color('danger')
            ->requiresConfirmation()
            ->action(function (array $arguments): void {
                $this->product->relatedProducts()->detach($arguments['id']);

                Notification::make()
                    ->title(__('shopper::pages/products.notifications.remove_related'))
                    ->success()
                    ->send();

                $this->redirect(
                    route('shopper.products.edit', ['product' => $this->product, 'tab' => 'related']),
                    navigate: true
                );
            });
    }

    /**
     * @return array<int>
     */
    #[Computed]
    public function productsIds(): array
    {
        return array_merge($this->product->relatedProducts->pluck('id')->toArray(), [$this->product->id]);
    }

    public function render(): View
    {
        return view('shopper::livewire.components.products.forms.related', [
            'relatedProducts' => $this->product->relatedProducts,
        ]);
    }
}

```

### packages/admin/src/Livewire/Components/Products/Form/Seo.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Products\Form;

use Filament\Forms\Components\KeyValue;
use Filament\Notifications\Notification;
use Filament\Schemas\Components\Group;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Schemas\Schema;
use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Model;
use Livewire\Component;
use Shopper\Components\Form\SeoField;
use Shopper\Core\Models\Contracts\Product;
use Shopper\Traits\HandlesAuthorizationExceptions;

/**
 * @property-read Schema $form
 */
class Seo extends Component implements HasSchemas
{
    use HandlesAuthorizationExceptions;
    use InteractsWithSchemas;

    /** @var Model&Product */
    public Product $product;

    /** @var array<string, mixed>|null */
    public ?array $data = [];

    public function mount(): void
    {
        $this->form->fill($this->product->toArray());
    }

    public function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                Group::make()
                    ->schema(SeoField::make()),
                KeyValue::make('metadata')
                    ->reorderable(),
            ])
            ->statePath('data')
            ->model($this->product);
    }

    public function store(): void
    {
        $this->product->update($this->form->getState());

        $this->dispatch('product.updated');

        Notification::make()
            ->body(__('shopper::pages/products.notifications.seo_update'))
            ->success()
            ->send();
    }

    public function render(): View
    {
        return view('shopper::livewire.components.products.forms.seo');
    }
}

```

### packages/admin/src/Livewire/Components/Products/Form/Shipping.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Products\Form;

use Filament\Notifications\Notification;
use Filament\Schemas\Components\Grid;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Schemas\Schema;
use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Model;
use Livewire\Component;
use Shopper\Components\Form\ShippingField;
use Shopper\Components\Section;
use Shopper\Core\Models\Contracts\Product;
use Shopper\Traits\HandlesAuthorizationExceptions;

/**
 * @property-read Schema $form
 */
class Shipping extends Component implements HasSchemas
{
    use HandlesAuthorizationExceptions;
    use InteractsWithSchemas;

    /** @var Model&Product */
    public Product $product;

    /** @var array<string, mixed>|null */
    public ?array $data = [];

    public function mount(): void
    {
        $this->form->fill($this->product->toArray());
    }

    public function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                Section::make(__('shopper::pages/products.shipping.package_dimension'))
                    ->aside()
                    ->compact()
                    ->extraAttributes(['class' => 'sh-section-aside'])
                    ->description(__('shopper::pages/products.shipping.package_dimension_description'))
                    ->schema([
                        Grid::make()->schema(ShippingField::make()),
                    ]),
            ])
            ->statePath('data')
            ->model($this->product);
    }

    public function store(): void
    {
        $this->product->update($this->form->getState());

        $this->dispatch('product.updated');

        Notification::make()
            ->title(__('shopper::pages/products.notifications.shipping_update'))
            ->success()
            ->send();
    }

    public function render(): View
    {
        return view('shopper::livewire.components.products.forms.shipping');
    }
}

```

### packages/admin/src/Livewire/Components/Products/Form/Variants.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Products\Form;

use Filament\Actions\Action;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Actions\DeleteAction;
use Filament\Actions\DeleteBulkAction;
use Filament\Notifications\Notification;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Tables\Columns\SpatieMediaLibraryImageColumn;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Concerns\InteractsWithTable;
use Filament\Tables\Contracts\HasTable;
use Filament\Tables\Table;
use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Collection;
use Illuminate\Support\Facades\Blade;
use Illuminate\Support\HtmlString;
use Livewire\Attributes\Lazy;
use Livewire\Component;
use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
use Shopper\Core\Models\Contracts\Product;
use Shopper\Core\Models\Contracts\ProductVariant;
use Shopper\Traits\HandlesAuthorizationExceptions;

#[Lazy]
class Variants extends Component implements HasActions, HasSchemas, HasTable
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;
    use InteractsWithTable;

    public Product $product;

    public function placeholder(): View
    {
        return view('shopper::components.skeleton.products.section');
    }

    public function table(Table $table): Table
    {
        return $table
            ->heading(__('shopper::pages/products.variants.title'))
            ->description(__('shopper::pages/products.variants.description'))
            ->query(
                resolve(ProductVariant::class)::query()
                    ->where('product_id', $this->product->id)
                    ->latest()
            )
            ->columns([
                SpatieMediaLibraryImageColumn::make('thumbnail')
                    ->collection(config('shopper.media.storage.thumbnail_collection'))
                    ->label(__('shopper::forms.label.thumbnail'))
                    ->circular(),
                TextColumn::make('name')
                    ->label(__('shopper::forms.label.name'))
                    ->searchable()
                    ->sortable(),
                TextColumn::make('sku')
                    ->label(__('shopper::layout.tables.sku'))
                    ->searchable()
                    ->sortable(),
                TextColumn::make('position')
                    ->label(__('shopper::forms.label.position'))
                    ->sortable(),
                TextColumn::make('stock')
                    ->label(__('shopper::layout.tables.current_stock'))
                    ->formatStateUsing(
                        fn (ProductVariant $record): HtmlString => new HtmlString(Blade::render(<<<BLADE
                            <div class="flex items-center">
                                <x-shopper::stock-badge :stock="{$record->stock}" />
                                {{ __('shopper::words.in_stock') }}
                            </div>
                        BLADE))
                    ),
            ])
            ->headerActions([
                Action::make('generate')
                    ->icon($this->product->type->getIcon())
                    ->label(__('shopper::pages/products.variants.generate'))
                    ->color('gray')
                    ->action(
                        fn () => $this->dispatch(
                            'openPanel',
                            component: 'shopper-slide-overs.generate-variants',
                            arguments: ['product' => $this->product]
                        )
                    )
                    ->visible($this->product->options->count() > 0),
                Action::make('add')
                    ->label(__('shopper::pages/products.variants.add'))
                    ->action(
                        fn () => $this->dispatch(
                            'openPanel',
                            component: 'shopper-slide-overs.add-variant',
                            arguments: ['product' => $this->product]
                        )
                    ),
            ])
            ->recordActions([
                Action::make('edit')
                    ->label(__('shopper::forms.actions.edit'))
                    ->iconButton()
                    ->icon(Untitledui::Edit03)
                    ->action(
                        fn (ProductVariant $record) => $this->redirectRoute(
                            name: 'shopper.products.variant',
                            parameters: ['product' => $this->product, 'variant' => $record],
                        ),
                    ),
                DeleteAction::make()
                    ->icon(Untitledui::Trash03)
                    ->iconButton()
                    ->modalIcon(Untitledui::Trash03)
                    ->successNotificationTitle(__('shopper::pages/products.notifications.variation_delete')),
            ])
            ->groupedBulkActions([
                DeleteBulkAction::make()
                    ->label(__('shopper::forms.actions.delete'))
                    ->requiresConfirmation()
                    ->action(function (Collection $records): void {
                        $records->each->delete();

                        Notification::make()
                            ->title(__('shopper::forms.actions.delete'))
                            ->body(
                                __('shopper::notifications.delete', [
                                    'item' => __('shopper::pages/products.variants.single'),
                                ])
                            )
                            ->success()
                            ->send();
                    })
                    ->deselectRecordsAfterCompletion(),
            ])
            ->emptyStateHeading(__('shopper::pages/products.variants.empty'))
            ->emptyStateIcon(Untitledui::BookOpen);
    }

    public function render(): View
    {
        return view('shopper::livewire.components.products.forms.variants');
    }
}

```

### packages/admin/src/Livewire/Components/Settings/Legal/PolicyForm.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Settings\Legal;

use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Forms\Components\Hidden;
use Filament\Forms\Components\RichEditor;
use Filament\Forms\Components\Toggle;
use Filament\Notifications\Notification;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Schemas\Schema;
use Illuminate\Contracts\View\View;
use Livewire\Component;
use Shopper\Core\Models\Legal;
use Shopper\Traits\HandlesAuthorizationExceptions;

/**
 * @property Schema $form
 */
class PolicyForm extends Component implements HasActions, HasSchemas
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;

    public Legal $legal;

    /**
     * @var array<string, mixed>|null
     */
    public ?array $data = [];

    public function mount(): void
    {
        $this->form->fill($this->legal->toArray());
    }

    public function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                Hidden::make('title')
                    ->unique(ignoreRecord: true),
                Toggle::make('is_enabled')
                    ->label(__('shopper::words.is_enabled'))
                    ->onColor('success'),
                RichEditor::make('content')
                    ->label(__('shopper::forms.label.content'))
                    ->id($this->legal->slug)
                    ->required(),
            ])
            ->statePath('data')
            ->model($this->legal);
    }

    public function store(): void
    {
        $this->legal->update(array_merge($this->form->getState(), [
            'slug' => $this->legal->slug,
        ]));

        Notification::make()
            ->title($this->legal->title)
            ->body(__('shopper::notifications.legal'))
            ->success()
            ->send();
    }

    public function render(): View
    {
        return view('shopper::livewire.components.settings.legal._form');
    }
}

```

### packages/admin/src/Livewire/Components/Settings/Legal/Privacy.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Settings\Legal;

use Illuminate\Contracts\View\View;
use Livewire\Component;
use Shopper\Core\Models\Legal;
use Shopper\Traits\HandlesAuthorizationExceptions;

class Privacy extends Component
{
    use HandlesAuthorizationExceptions;

    public Legal $legal;

    public function render(): View
    {
        return view('shopper::livewire.components.settings.legal.index', [
            'title' => __('shopper::pages/settings/global.legal.privacy'),
            'description' => __('shopper::pages/settings/global.legal.summary', ['policy' => __('shopper::pages/settings/global.legal.privacy')]),
        ]);
    }
}

```

### packages/admin/src/Livewire/Components/Settings/Legal/Refund.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Settings\Legal;

use Illuminate\Contracts\View\View;
use Livewire\Component;
use Shopper\Core\Models\Legal;
use Shopper\Traits\HandlesAuthorizationExceptions;

class Refund extends Component
{
    use HandlesAuthorizationExceptions;

    public Legal $legal;

    public function render(): View
    {
        return view('shopper::livewire.components.settings.legal.index', [
            'title' => __('shopper::pages/settings/global.legal.refund'),
            'description' => __('shopper::pages/settings/global.legal.summary', ['policy' => __('shopper::pages/settings/global.legal.refund')]),
        ]);
    }
}

```

### packages/admin/src/Livewire/Components/Settings/Legal/Shipping.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Settings\Legal;

use Illuminate\Contracts\View\View;
use Livewire\Component;
use Shopper\Core\Models\Legal;
use Shopper\Traits\HandlesAuthorizationExceptions;

class Shipping extends Component
{
    use HandlesAuthorizationExceptions;

    public Legal $legal;

    public function render(): View
    {
        return view('shopper::livewire.components.settings.legal.index', [
            'title' => __('shopper::pages/settings/global.legal.shipping'),
            'description' => __('shopper::pages/settings/global.legal.summary', ['policy' => __('shopper::pages/settings/global.legal.shipping')]),
        ]);
    }
}

```

### packages/admin/src/Livewire/Components/Settings/Legal/Terms.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Settings\Legal;

use Illuminate\Contracts\View\View;
use Livewire\Component;
use Shopper\Core\Models\Legal;
use Shopper\Traits\HandlesAuthorizationExceptions;

class Terms extends Component
{
    use HandlesAuthorizationExceptions;

    public Legal $legal;

    public function render(): View
    {
        return view('shopper::livewire.components.settings.legal.index', [
            'title' => __('shopper::pages/settings/global.legal.terms_of_use'),
            'description' => __('shopper::pages/settings/global.legal.summary', ['policy' => __('shopper::pages/settings/global.legal.terms_of_use')]),
        ]);
    }
}

```

### packages/admin/src/Livewire/Components/Settings/Locations/InventoryForm.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Settings\Locations;

use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Forms\Components\Hidden;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\Toggle;
use Filament\Notifications\Notification;
use Filament\Schemas\Components\Utilities\Set;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Schemas\Schema;
use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Str;
use Livewire\Component;
use Shopper\Components\Form\AddressField;
use Shopper\Components\Section;
use Shopper\Components\Separator;
use Shopper\Core\Models\Contracts\Inventory;
use Shopper\Traits\HandlesAuthorizationExceptions;

/**
 * @property-read Schema $form
 */
class InventoryForm extends Component implements HasActions, HasSchemas
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;

    public Model&Inventory $inventory;

    /** @var array<string, mixed>|null */
    public ?array $data = [];

    public function mount(): void
    {
        $this->form->fill($this->inventory->toArray());
    }

    public function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                Section::make(__('shopper::pages/settings/global.location.detail'))
                    ->aside()
                    ->compact()
                    ->description(__('shopper::pages/settings/global.location.detail_summary'))
                    ->extraAttributes(['class' => 'sh-section-aside'])
                    ->schema([
                        TextInput::make('name')
                            ->label(__('shopper::forms.label.name'))
                            ->placeholder('White House')
                            ->required()
                            ->live(onBlur: true)
                            ->afterStateUpdated(function (string $operation, ?string $state, Set $set): void {
                                if ($state) {
                                    $set('code', Str::slug($state));
                                }
                            }),
                        Hidden::make('code'),
                        TextInput::make('email')
                            ->label(__('shopper::forms.label.email'))
                            ->autocomplete('email-address')
                            ->email()
                            ->unique(ignoreRecord: true)
                            ->required(),
                        Textarea::make('description')
                            ->label(__('shopper::forms.label.description'))
                            ->rows(3)
                            ->columnSpan('full'),
                        Toggle::make('is_default')
                            ->label(__('shopper::pages/settings/global.location.set_default'))
                            ->helperText(__('shopper::pages/settings/global.location.set_default_summary')),
                        TextInput::make('priority')
                            ->label(__('shopper::forms.label.priority'))
                            ->helperText(__('shopper::pages/settings/global.location.priority_summary'))
                            ->numeric()
                            ->default(0)
                            ->minValue(0)
                            ->required(),
                    ])
                    ->columns(),
                Separator::make(),
                Section::make(__('shopper::pages/settings/global.location.address'))
                    ->aside()
                    ->compact()
                    ->description(__('shopper::pages/settings/global.location.address_summary'))
                    ->extraAttributes(['class' => 'sh-section-aside'])
                    ->schema(AddressField::make())
                    ->columns(),
            ])
            ->statePath('data')
            ->model($this->inventory);
    }

    public function store(): void
    {
        if ($this->inventory->id) {
            $this->inventory->update($this->form->getState());
        } else {
            resolve(Inventory::class)::query()->create($this->form->getState());
        }

        Notification::make()
            ->title(__('shopper::notifications.save', ['item' => __('shopper::pages/settings/global.location.single')]))
            ->success()
            ->send();

        $this->redirectRoute(name: 'shopper.settings.locations', navigate: true);
    }

    public function render(): View
    {
        return view('shopper::livewire.components.settings.locations._form');
    }
}

```

### packages/admin/src/Livewire/Components/Settings/Team/Permissions.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Settings\Team;

use Filament\Notifications\Notification;
use Illuminate\Contracts\View\View;
use Livewire\Attributes\On;
use Livewire\Component;
use Shopper\Models\Permission;
use Shopper\Models\Role;
use Shopper\Traits\HandlesAuthorizationExceptions;

class Permissions extends Component
{
    use HandlesAuthorizationExceptions;

    public Role $role;

    public function mount(): void
    {
        $this->authorize('view_users');
    }

    public function togglePermission(int $id): void
    {
        $this->authorize('view_users');
        /** @var Permission $permission */
        $permission = Permission::query()->find($id);

        if ($this->role->hasPermissionTo($permission->name)) {
            $this->role->revokePermissionTo($permission->name);

            Notification::make()
                ->title(__('shopper::notifications.users_roles.permission_revoke', ['permission' => $permission->display_name]))
                ->success()
                ->send();
        } else {
            $this->role->givePermissionTo($permission->name);

            Notification::make()
                ->title(__('shopper::notifications.users_roles.permission_allow', ['permission' => $permission->display_name]))
                ->success()
                ->send();
        }
    }

    public function removePermission(int $id): void
    {
        $this->authorize('view_users');

        Permission::query()->find($id)->delete();

        Notification::make()
            ->title(__('shopper::notifications.delete', ['item' => __('shopper::pages/settings/staff.permission')]))
            ->success()
            ->send();
    }

    #[On('permissionAdded')]
    public function render(): View
    {
        return view('shopper::livewire.components.settings.team.permissions', [
            'groupPermissions' => Permission::query()
                ->with('users')
                ->orderBy('created_at')
                ->get()
                ->groupBy('group_name'),
        ]);
    }
}

```

### packages/admin/src/Livewire/Components/Settings/Team/UsersRole.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Components\Settings\Team;

use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Actions\DeleteAction;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Columns\ViewColumn;
use Filament\Tables\Concerns\InteractsWithTable;
use Filament\Tables\Contracts\HasTable;
use Filament\Tables\Table;
use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Builder;
use Livewire\Component;
use Shopper\Models\Contracts\ShopperUser;
use Shopper\Models\Role;
use Shopper\Traits\HandlesAuthorizationExceptions;

class UsersRole extends Component implements HasActions, HasSchemas, HasTable
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;
    use InteractsWithTable;

    public Role $role;

    public function table(Table $table): Table
    {
        $userModel = config('auth.providers.users.model');

        return $table
            ->query(
                $userModel::query()
                    ->with('roles')
                    ->whereHas('roles', function (Builder $query): void {
                        $query->where('name', $this->role->name);
                    })
            )
            ->columns([
                ViewColumn::make('full_name')
                    ->label(__('shopper::forms.label.full_name'))
                    ->view('shopper::livewire.tables.cells.administrators.name'),
                TextColumn::make('email')
                    ->label(__('shopper::forms.label.email'))
                    ->icon(fn (ShopperUser $record): string => $record->email_verified_at ? 'untitledui-check-verified-02' : 'untitledui-alert-circle')
                    ->iconColor(fn (ShopperUser $record): string => $record->email_verified_at ? 'success' : 'danger'),
                TextColumn::make('roles_label')
                    ->label(__('shopper::forms.label.role'))
                    ->badge(),
                TextColumn::make('id')
                    ->label(__('shopper::forms.label.access'))
                    ->color('gray')
                    ->formatStateUsing(
                        fn (ShopperUser $record): string|array|null => $record->hasRole(config('shopper.admin.roles.admin'))
                        ? __('shopper::words.full')
                        : __('shopper::words.limited')
                    ),
            ])
            ->recordActions([
                DeleteAction::make('delete')
                    ->label(__('shopper::forms.actions.delete'))
                    ->visible(fn (ShopperUser $record): bool => shopper()->auth()->user()->isAdmin() && ! $record->isAdmin()) // @phpstan-ignore-line
                    ->successNotificationTitle(__('shopper::notifications.users_roles.admin_deleted')),
            ])
            ->emptyStateIcon('untitledui-users')
            ->emptyStateHeading(__('shopper::words.no_users'));
    }

    public function render(): View
    {
        return view('shopper::livewire.components.settings.team.users-role');
    }
}

```

### packages/admin/src/Livewire/Pages/Collection/Edit.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Pages\Collection;

use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Forms\Components\DateTimePicker;
use Filament\Forms\Components\KeyValue;
use Filament\Forms\Components\RichEditor;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\SpatieMediaLibraryFileUpload;
use Filament\Forms\Components\TextInput;
use Filament\Infolists\Components\TextEntry;
use Filament\Notifications\Notification;
use Filament\Schemas\Components\Grid;
use Filament\Schemas\Components\Group;
use Filament\Schemas\Components\Livewire;
use Filament\Schemas\Components\Utilities\Set;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Schemas\Schema;
use Illuminate\Contracts\View\View;
use Illuminate\Support\Facades\Blade;
use Illuminate\Support\HtmlString;
use Illuminate\Support\Str;
use Shopper\Components\Form\SeoField;
use Shopper\Core\Models\Contracts\Collection;
use Shopper\Livewire\Components\Collection\CollectionProducts;
use Shopper\Livewire\Pages\AbstractPageComponent;
use Shopper\Traits\HandlesAuthorizationExceptions;

/**
 * @property-read Schema $form
 */
class Edit extends AbstractPageComponent implements HasActions, HasSchemas
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;

    public ?Collection $collection = null;

    /** @var array<string, mixed>|null */
    public ?array $data = [];

    public function mount(): void
    {
        $this->authorize('edit_collections');

        $this->collection?->load('rules');

        $this->form->fill($this->collection?->toArray() ?? []);
    }

    public function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                Group::make()
                    ->schema([
                        Grid::make()
                            ->schema([
                                TextInput::make('name')
                                    ->label(__('shopper::forms.label.name'))
                                    ->placeholder('Summers Collections, Christmas promotions...')
                                    ->required()
                                    ->live(onBlur: true)
                                    ->afterStateUpdated(function (string $operation, ?string $state, Set $set): void {
                                        if ($state) {
                                            $set('slug', Str::slug($state));
                                        }
                                    }),
                                TextInput::make('slug')
                                    ->label(__('shopper::forms.label.slug'))
                                    ->disabled()
                                    ->dehydrated()
                                    ->required()
                                    ->maxLength(255)
                                    ->unique(config('shopper.models.collection'), 'slug', ignoreRecord: true),
                            ]),
                        RichEditor::make('description')
                            ->label(__('shopper::forms.label.description'))
                            ->toolbarButtons([
                                ['bold', 'italic', 'link', 'strike', 'underline'],
                                ['bulletList', 'orderedList', 'table', 'attachFiles'],
                                ['undo', 'redo'],
                            ]),
                        Livewire::make(CollectionProducts::class, ['collection' => $this->collection]),
                    ])
                    ->columnSpan(['lg' => 2]),
                Group::make()
                    ->schema([
                        SpatieMediaLibraryFileUpload::make('file')
                            ->label(__('shopper::forms.label.image_preview'))
                            ->collection(config('shopper.media.storage.thumbnail_collection'))
                            ->image()
                            ->maxSize(config('shopper.media.max_size.thumbnail')),
                        DateTimePicker::make('published_at')
                            ->label(__('shopper::forms.label.availability'))
                            ->native(false)
                            ->required()
                            ->default(now())
                            ->helperText(__('shopper::pages/collections.availability_description')),
                        Select::make('zones')
                            ->label(__('shopper::pages/settings/zones.title'))
                            ->relationship('zones', 'name')
                            ->multiple()
                            ->native(false)
                            ->searchable()
                            ->preload()
                            ->helperText(__('shopper::pages/collections.zone_description')),
                        Group::make()
                            ->schema([
                                TextEntry::make(__('shopper::words.seo.slug'))
                                    ->label(__('shopper::words.seo.title'))
                                    ->state(new HtmlString(Blade::render(<<<'BLADE'
                                        <p class="max-w-2xl text-sm text-gray-500 dark:text-gray-400">
                                            {{ __('shopper::words.seo.description', ['name' => __('shopper::pages/collections.single')]) }}
                                        </p>
                                    BLADE))),
                                ...SeoField::make(),
                            ]),
                        KeyValue::make('metadata')->reorderable(),
                    ])
                    ->columnSpan(['lg' => 1]),
            ])
            ->columns(3)
            ->statePath('data')
            ->model($this->collection); // @phpstan-ignore-line
    }

    public function store(): void
    {
        $this->collection->update($this->form->getState());

        Notification::make()
            ->title(__('shopper::notifications.update', ['item' => __('shopper::pages/collections.single')]))
            ->success()
            ->send();
    }

    public function render(): View
    {
        return view('shopper::livewire.pages.collections.edit')
            ->title(__('shopper::forms.actions.edit_label', ['label' => $this->collection->name]));
    }
}

```

### packages/admin/src/Livewire/Pages/Customers/Create.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Pages\Customers;

use Filament\Actions\Action;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Forms\Components\Checkbox;
use Filament\Forms\Components\Hidden;
use Filament\Forms\Components\TextInput;
use Filament\Notifications\Notification;
use Filament\Schemas\Components\Utilities\Set;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Schemas\Schema;
use Illuminate\Contracts\View\View;
use Illuminate\Support\Arr;
use Illuminate\Support\Collection;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;
use Illuminate\Validation\ValidationException;
use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
use Shopper\Components\Form\AddressField;
use Shopper\Components\Form\GenderField;
use Shopper\Components\Section;
use Shopper\Components\Separator;
use Shopper\Core\Enum\AddressType;
use Shopper\Core\Models\Country;
use Shopper\Livewire\Pages\AbstractPageComponent;
use Shopper\Models\Contracts\ShopperUser;
use Shopper\Notifications\CustomerSendCredentials;
use Shopper\Traits\HandlesAuthorizationExceptions;

/**
 * @property-read Schema $form
 */
class Create extends AbstractPageComponent implements HasActions, HasSchemas
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;

    /** @var array<string, mixed>|null */
    public ?array $data = [];

    public function mount(): void
    {
        $this->authorize('add_customers');

        $this->form->fill();
    }

    public function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                Section::make(__('shopper::pages/customers.overview'))
                    ->aside()
                    ->compact()
                    ->columns()
                    ->description(__('shopper::pages/customers.overview_description'))
                    ->extraAttributes(['class' => 'sh-section-aside'])
                    ->schema([
                        TextInput::make('first_name')
                            ->label(__('shopper::forms.label.first_name'))
                            ->required(),
                        TextInput::make('last_name')
                            ->label(__('shopper::forms.label.last_name'))
                            ->required(),
                        TextInput::make('email')
                            ->label(__('shopper::forms.label.email'))
                            ->prefixIcon(Untitledui::Mail)
                            ->autocomplete('email-address')
                            ->email()
                            ->unique()
                            ->required(),
                        TextInput::make('phone_number')
                            ->label(__('shopper::forms.label.phone_number'))
                            ->hint(__('shopper::forms.label.optional'))
                            ->tel(),
                        GenderField::make(),
                    ]),
                Separator::make(),
                Section::make(__('shopper::pages/customers.security_title'))
                    ->aside()
                    ->compact()
                    ->description(__('shopper::pages/customers.security_description'))
                    ->extraAttributes(['class' => 'sh-section-aside'])
                    ->schema([
                        TextInput::make('password')
                            ->label(__('shopper::forms.label.password'))
                            ->password()
                            ->revealable()
                            ->required()
                            ->hintAction(
                                Action::make(__('shopper::words.generate'))
                                    ->color('info')
                                    ->action(function (Set $set): void {
                                        $set('password', Str::password(12));
                                    }),
                            )
                            ->confirmed()
                            ->dehydrateStateUsing(fn (string $state): string => Hash::make($state)),
                        TextInput::make('password_confirmation')
                            ->label(__('shopper::forms.label.confirm_password'))
                            ->password()
                            ->revealable()
                            ->required(),
                        Hidden::make('_password'),
                    ]),
                Separator::make(),
                Section::make(__('shopper::pages/customers.address_title'))
                    ->aside()
                    ->compact()
                    ->columns()
                    ->description(__('shopper::pages/customers.address_description'))
                    ->extraAttributes(['class' => 'sh-section-aside'])
                    ->schema(AddressField::make('address')),
                Separator::make(),
                Section::make(__('shopper::pages/customers.notification_title'))
                    ->aside()
                    ->compact()
                    ->columns()
                    ->description(__('shopper::pages/customers.notification_description'))
                    ->extraAttributes(['class' => 'sh-section-aside'])
                    ->schema([
                        Checkbox::make('opt_in')
                            ->label(__('shopper::pages/customers.marketing_email'))
                            ->helperText(__('shopper::pages/customers.marketing_description')),
                        Checkbox::make('send_mail')
                            ->label(__('shopper::pages/customers.send_credentials'))
                            ->helperText(__('shopper::pages/customers.credential_description')),
                    ]),
            ])
            ->statePath('data')
            ->model(config('auth.providers.users.model'));
    }

    public function store(): void
    {
        /** @var array<string, mixed> $data */
        $data = $this->form->getState();
        $sendMail = data_get($data, 'send_mail');
        $password = data_get($data, 'password_confirmation');

        $customerData = Arr::except($data, ['address', 'send_mail', 'password_confirmation']);
        $address = array_merge(Arr::only($data, ['address'])['address'], [
            'first_name' => $data['first_name'],
            'last_name' => $data['last_name'],
            'type' => AddressType::Shipping,
        ]);

        $userModel = config('auth.providers.users.model');

        /** @var ShopperUser $customer */
        $customer = $userModel::create(array_merge(
            $customerData,
            ['email_verified_at' => now()->toDateTimeString()],
        ));

        $customer->assignRole(config('shopper.admin.roles.user'));
        $customer->addresses()->create($address);

        if ($sendMail) {
            $customer->notify(new CustomerSendCredentials($password));
        }

        Notification::make()
            ->title(__('shopper::notifications.create', ['item' => __('shopper::pages/customers.single')]))
            ->success()
            ->send();

        $this->redirectRoute(name: 'shopper.customers.index', navigate: true);
    }

    public function render(): View
    {
        return view('shopper::livewire.pages.customers.create', [
            'countries' => Cache::get(
                key: 'countries-settings',
                default: fn (): Collection => Country::query()->orderBy('name')->get()
            ),
        ])
            ->title(__('shopper::forms.actions.add_label', ['label' => __('shopper::pages/customers.single')]));
    }

    protected function onValidationError(ValidationException $exception): void
    {
        Notification::make()
            ->title($exception->getMessage())
            ->danger()
            ->send();
    }
}

```

### packages/admin/src/Livewire/Pages/Customers/Show.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Pages\Customers;

use Filament\Actions\Action;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Notifications\Notification;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Str;
use Livewire\Attributes\Url;
use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
use Shopper\Livewire\Pages\AbstractPageComponent;
use Shopper\Models\Contracts\ShopperUser;
use Shopper\Traits\HandlesAuthorizationExceptions;

class Show extends AbstractPageComponent implements HasActions, HasSchemas
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;

    public ShopperUser $customer;

    #[Url(as: 'tab')]
    public string $activeTab = 'profile';

    public function mount(int $user): void
    {
        $this->authorize('read_customers');

        $userModel = config('auth.providers.users.model');

        /** @var ShopperUser $customer */
        $customer = $userModel::query()->with(['addresses', 'orders'])->findOrFail($user);

        $this->customer = $customer;
    }

    public function anonymizeAction(): Action
    {
        return Action::make('anonymize')
            ->label(__('shopper::pages/customers.anonymize.action'))
            ->authorize('delete_customers', $this->customer) // @phpstan-ignore-line
            ->icon(Untitledui::UserX02)
            ->modalIcon(Untitledui::UserX02)
            ->modalHeading(__('shopper::pages/customers.anonymize.title'))
            ->modalDescription(__('shopper::pages/customers.anonymize.description'))
            ->modalSubmitActionLabel(__('shopper::pages/customers.anonymize.confirm'))
            ->visible(shopper()->auth()->user()->can('delete_customers'))
            ->requiresConfirmation()
            ->color('danger')
            ->action(function (): void {
                /** @var Model&ShopperUser $customer */
                $customer = $this->customer;

                $customer->update([
                    'first_name' => __('shopper::pages/customers.anonymize.first_name'),
                    'last_name' => __('shopper::pages/customers.anonymize.last_name'),
                    'email' => 'anonymized_'.$customer->id.'_'.Str::random(8).'@anonymized.local',
                    'phone_number' => null,
                    'avatar_type' => 'gravatar',
                    'avatar_location' => null,
                    'birth_date' => null,
                    'last_login_ip' => null,
                    'opt_in' => false,
                ]);

                $customer->addresses()->delete();

                Notification::make()
                    ->title(__('shopper::pages/customers.anonymize.success'))
                    ->success()
                    ->send();

                $this->redirectRoute(name: 'shopper.customers.index', navigate: true);
            });
    }

    public function render(): View
    {
        /** @var Model&ShopperUser $customer */
        $customer = $this->customer;

        return view('shopper::livewire.pages.customers.show')
            ->title(__('shopper::forms.actions.show_label', ['label' => $customer->full_name]));
    }
}

```

### packages/admin/src/Livewire/Pages/Order/Detail.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Pages\Order;

use Filament\Actions\Action;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Notifications\Notification;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Illuminate\Contracts\View\View;
use Livewire\Attributes\On;
use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
use Shopper\Core\Enum\OrderStatus;
use Shopper\Core\Enum\PaymentStatus;
use Shopper\Core\Events\Orders\OrderArchived;
use Shopper\Core\Events\Orders\OrderCancelled;
use Shopper\Core\Events\Orders\OrderCompleted;
use Shopper\Core\Events\Orders\OrderPaid;
use Shopper\Core\Models\Contracts\Order;
use Shopper\Livewire\Pages\AbstractPageComponent;
use Shopper\Payment\Services\PaymentProcessingService;
use Shopper\Traits\HandlesAuthorizationExceptions;

class Detail extends AbstractPageComponent implements HasActions, HasSchemas
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;

    public Order $order;

    public function mount(): void
    {
        $this->authorize('read_orders');

        $this->order->load('customer', 'channel');
    }

    public function goToOrder(int $id): void
    {
        $this->redirectRoute('shopper.orders.detail', $id, navigate: true);
    }

    public function cancelOrderAction(): Action
    {
        return Action::make('cancelOrder')
            ->label(__('shopper::forms.actions.cancel_order'))
            ->visible($this->order->canBeCancelled())
            ->action(function (): void {
                $this->order->update([
                    'status' => OrderStatus::Cancelled,
                    'cancelled_at' => now(),
                ]);

                $this->order->refresh();
                $this->dispatch('order.updated');

                event(new OrderCancelled($this->order));

                Notification::make()
                    ->title(__('shopper::pages/orders.notifications.cancelled'))
                    ->success()
                    ->send();
            });
    }

    public function startProcessingAction(): Action
    {
        return Action::make('startProcessing')
            ->label(__('shopper::forms.actions.start_processing'))
            ->visible($this->order->isNew())
            ->action(function (): void {
                $this->order->update(['status' => OrderStatus::Processing]);

                $this->order->refresh();
                $this->dispatch('order.updated');

                Notification::make()
                    ->title(__('shopper::pages/orders.notifications.processing'))
                    ->success()
                    ->send();
            });
    }

    public function markPaidAction(): Action
    {
        return Action::make('markPaid')
            ->label(__('shopper::forms.actions.mark_paid'))
            ->visible($this->order->isPaymentPending() || $this->order->isPaymentAuthorized())
            ->action(function (): void {
                $data = ['payment_status' => PaymentStatus::Paid];

                if ($this->order->isNew()) {
                    $data['status'] = OrderStatus::Processing;
                }

                $this->order->update($data);

                $this->order->refresh();
                $this->dispatch('order.updated');

                event(new OrderPaid($this->order));

                Notification::make()
                    ->title(__('shopper::pages/orders.notifications.paid'))
                    ->success()
                    ->send();
            });
    }

    public function markCompleteAction(): Action
    {
        return Action::make('markComplete')
            ->label(__('shopper::forms.actions.mark_complete'))
            ->visible($this->order->isProcessing() && $this->order->isPaid())
            ->action(function (): void {
                $this->order->update(['status' => OrderStatus::Completed]);

                $this->order->refresh();
                $this->dispatch('order.updated');

                event(new OrderCompleted($this->order));

                Notification::make()
                    ->title(__('shopper::pages/orders.notifications.completed'))
                    ->success()
                    ->send();
            });
    }

    public function capturePaymentAction(): Action
    {
        return Action::make('capturePayment')
            ->label(__('shopper::forms.actions.capture_payment'))
            ->icon(Untitledui::CreditCardDown)
            ->visible($this->order->isPaymentAuthorized())
            ->requiresConfirmation()
            ->modalIcon(Untitledui::CreditCardDown)
            ->modalHeading(__('shopper::pages/orders.modals.capture_heading', ['number' => $this->order->number]))
            ->modalDescription(__('shopper::pages/orders.modals.capture_notice'))
            ->modalSubmitActionLabel(__('shopper::forms.actions.confirm'))
            ->action(function (): void {
                $service = resolve(PaymentProcessingService::class);
                $reference = $service->getLatestReference($this->order);

                if (! $reference) {
                    Notification::make()
                        ->title(__('shopper::pages/orders.notifications.capture_no_reference'))
                        ->danger()
                        ->send();

                    return;
                }

                $result = $service->capture($this->order, $reference);

                if (! $result->success) {
                    Notification::make()
                        ->title($result->message ?? __('shopper::pages/orders.notifications.capture_failed'))
                        ->danger()
                        ->send();

                    return;
                }

                $this->order->refresh();
                $this->dispatch('order.updated');

                Notification::make()
                    ->title(__('shopper::pages/orders.notifications.captured'))
                    ->success()
                    ->send();
            });
    }

    public function archiveAction(): Action
    {
        return Action::make('archive')
            ->label(__('shopper::forms.actions.archive'))
            ->color('danger')
            ->icon(Untitledui::Archive)
            ->visible(! $this->order->isCompleted() && ! $this->order->isPaid())
            ->requiresConfirmation()
            ->modalHeading(__('shopper::pages/orders.modals.archived_number', ['number' => $this->order->number]))
            ->modalDescription(__('shopper::pages/orders.modals.archived_notice'))
            ->modalSubmitActionLabel(__('shopper::forms.actions.confirm'))
            ->action(function (): void {
                $this->order->update([
                    'status' => OrderStatus::Archived,
                    'archived_at' => now(),
                ]);

                event(new OrderArchived($this->order));

                Notification::make()
                    ->title(__('shopper::notifications.orders.archived'))
                    ->success()
                    ->send();

                $this->redirectRoute('shopper.orders.index', navigate: true);
            });
    }

    #[On('order.shipping.created')]
    public function render(): View
    {
        return view('shopper::livewire.pages.orders.detail', [
            'nextOrder' => resolve(Order::class)::query()
                ->where('id', '>', $this->order->id)
                ->oldest('id')
                ->first(),
            'prevOrder' => resolve(Order::class)::query()
                ->where('id', '<', $this->order->id)
                ->latest('id')
                ->first(),
        ])
            ->title(__('shopper::pages/orders.show_title', ['number' => $this->order->number]));
    }
}

```

### packages/admin/src/Livewire/Pages/Order/Shipments.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Pages\Order;

use Filament\Actions\Action;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\TextInput;
use Filament\Notifications\Notification;
use Filament\Resources\Concerns\HasTabs;
use Filament\Schemas\Components\Tabs\Tab;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Support\Enums\Width;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Columns\ViewColumn;
use Filament\Tables\Concerns\InteractsWithTable;
use Filament\Tables\Contracts\HasTable;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Table;
use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Builder;
use Livewire\Attributes\On;
use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
use Shopper\Core\Actions\MarkShipmentDeliveredAction;
use Shopper\Core\Enum\ShipmentStatus;
use Shopper\Core\Models\OrderShipping;
use Shopper\Livewire\Pages\AbstractPageComponent;
use Shopper\Shipping\Services\CarrierRateService;
use Shopper\Traits\HandlesAuthorizationExceptions;

class Shipments extends AbstractPageComponent implements HasActions, HasSchemas, HasTable
{
    use HandlesAuthorizationExceptions;
    use HasTabs;
    use InteractsWithActions;
    use InteractsWithSchemas;
    use InteractsWithTable;

    public function mount(): void
    {
        $this->authorize('browse_orders');

        $this->loadDefaultActiveTab();
    }

    #[On('shipment-updated')]
    public function refreshTable(): void
    {
        $this->resetTable();
    }

    /**
     * @return array<string, Tab>
     */
    public function getTabs(): array
    {
        return [
            'all' => Tab::make(__('shopper::words.all'))
                ->icon(Untitledui::LayersThree)
                ->badge(fn (): int => OrderShipping::query()->count()),
            'pending' => Tab::make(ShipmentStatus::Pending->getLabel())
                ->icon(ShipmentStatus::Pending->getIcon())
                ->badge(fn (): int => OrderShipping::query()->where('status', ShipmentStatus::Pending)->count())
                ->badgeColor('warning')
                ->query(fn (Builder $query): Builder => $query->where('status', ShipmentStatus::Pending)),
            'in_transit' => Tab::make(ShipmentStatus::InTransit->getLabel())
                ->icon(ShipmentStatus::InTransit->getIcon())
                ->badge(fn (): int => OrderShipping::query()->whereIn('status', [
                    ShipmentStatus::PickedUp,
                    ShipmentStatus::InTransit,
                    ShipmentStatus::AtSortingCenter,
                    ShipmentStatus::OutForDelivery,
                ])->count())
                ->badgeColor('primary')
                ->query(fn (Builder $query): Builder => $query->whereIn('status', [
                    ShipmentStatus::PickedUp,
                    ShipmentStatus::InTransit,
                    ShipmentStatus::AtSortingCenter,
                    ShipmentStatus::OutForDelivery,
                ])),
            'delivered' => Tab::make(ShipmentStatus::Delivered->getLabel())
                ->icon(ShipmentStatus::Delivered->getIcon())
                ->badge(fn (): int => OrderShipping::query()->where('status', ShipmentStatus::Delivered)->count())
                ->badgeColor('success')
                ->query(fn (Builder $query): Builder => $query->where('status', ShipmentStatus::Delivered)),
            'failed' => Tab::make(ShipmentStatus::DeliveryFailed->getLabel())
                ->icon(ShipmentStatus::DeliveryFailed->getIcon())
                ->badge(fn (): int => OrderShipping::query()->where('status', ShipmentStatus::DeliveryFailed)->count())
                ->badgeColor('danger')
                ->query(fn (Builder $query): Builder => $query->where('status', ShipmentStatus::DeliveryFailed)),
        ];
    }

    public function table(Table $table): Table
    {
        return $table
            ->query(
                OrderShipping::query()
                    ->with(['order', 'carrier', 'items', 'events'])
                    ->latest()
            )
            ->modifyQueryUsing($this->modifyQueryWithActiveTab(...))
            ->columns([
                TextColumn::make('id')
                    ->label(__('shopper::pages/orders.shipment_id'))
                    ->formatStateUsing(fn (OrderShipping $record): string => 'SHP-'.$record->id)
                    ->searchable()
                    ->sortable(),
                ViewColumn::make('shipment_event')
                    ->label(__('shopper::pages/orders.shipment_event'))
                    ->view('shopper::livewire.tables.cells.orders.shipment-stepper'),
                TextColumn::make('status')
                    ->label(__('shopper::forms.label.status'))
                    ->badge()
                    ->color(fn (OrderShipping $record): ?string => $record->status?->getColor())
                    ->icon(fn (OrderShipping $record): ?string => $record->status?->getIcon())
                    ->formatStateUsing(fn (OrderShipping $record): string => $record->status?->getLabel() ?? '—'),
                TextColumn::make('shipped_at')
                    ->label(__('shopper::forms.label.shipped_at'))
                    ->date()
                    ->sortable(),
                TextColumn::make('order.number')
                    ->label(__('shopper::pages/orders.order_number'))
                    ->searchable()
                    ->sortable()
                    ->url(fn (OrderShipping $record): string => route('shopper.orders.detail', $record->order)),
                ViewColumn::make('carrier')
                    ->label(__('shopper::pages/orders.carrier_service'))
                    ->view('shopper::livewire.tables.cells.orders.shipment-carrier'),
            ])
            ->recordActions([
                Action::make('markDelivered')
                    ->label(__('shopper::forms.actions.mark_delivered'))
                    ->icon(Untitledui::PackageCheck)
                    ->color('success')
                    ->visible(fn (OrderShipping $record): bool => $record->canBeDelivered())
                    ->requiresConfirmation()
                    ->action(function (OrderShipping $record): void {
                        (new MarkShipmentDeliveredAction)->execute($record);

                        Notification::make()
                            ->title(__('shopper::pages/orders.notifications.shipment_delivered'))
                            ->success()
                            ->send();
                    }),
                Action::make('edit')
                    ->label(__('shopper::forms.actions.edit'))
                    ->icon(Untitledui::Edit03)
                    ->iconButton()
                    ->modalWidth(Width::Large)
                    ->fillForm(fn (OrderShipping $record): array => [
                        'carrier_id' => $record->carrier_id,
                        'tracking_number' => $record->tracking_number,
                        'tracking_url' => $record->tracking_url,
                    ])
                    ->schema([
                        Select::make('carrier_id')
                            ->label(__('shopper::pages/orders.carrier_service'))
                            ->options(fn (): array => resolve(CarrierRateService::class)->getCarrierSelectOptions())
                            ->native(false)
                            ->searchable()
                            ->allowHtml()
                            ->required(),
                        TextInput::make('tracking_number')
                            ->label(__('shopper::forms.label.tracking_number'))
                            ->placeholder('e.g. 1Z999AA10123456784'),
                        TextInput::make('tracking_url')
                            ->label(__('shopper::forms.label.tracking_url'))
                            ->placeholder('https://your-tracking-url.com')
                            ->url(),
                    ])
                    ->action(function (OrderShipping $record, array $data): void {
                        $record->update($data);

                        Notification::make()
                            ->title(__('shopper::notifications.update', ['item' => __('shopper::pages/orders.shipments')]))
                            ->success()
                            ->send();
                    }),
                Action::make('view')
                    ->label(__('shopper::pages/orders.shipment.manage'))
                    ->icon(Untitledui::Sliders)
                    ->iconButton()
                    ->tooltip(__('shopper::pages/orders.shipment.manage'))
                    ->action(fn (OrderShipping $record) => $this->dispatch(
                        'openPanel',
                        component: 'shopper-slide-overs.shipment-detail',
                        arguments: ['shipment' => $record],
                    )),
            ])
            ->filters([
                SelectFilter::make('status')
                    ->label(__('shopper::forms.label.status'))
                    ->options(ShipmentStatus::options())
                    ->multiple(),
                SelectFilter::make('order_id')
                    ->label(__('shopper::pages/orders.order_number'))
                    ->relationship('order', 'number', fn (Builder $query): Builder => $query->whereHas('shippings'))
                    ->searchable()
                    ->preload()
                    ->optionsLimit(10),
                SelectFilter::make('carrier_id')
                    ->label(__('shopper::pages/orders.carrier_service'))
                    ->relationship('carrier', 'name')
                    ->searchable()
                    ->preload(),
            ]);
    }

    public function render(): View
    {
        return view('shopper::livewire.pages.orders.shipments')
            ->title(__('shopper::pages/orders.shipments'));
    }
}

```

### packages/admin/src/Livewire/Pages/Product/Edit.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Pages\Product;

use Filament\Actions\Action;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Notifications\Notification;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Model;
use Livewire\Attributes\On;
use Livewire\Attributes\Url;
use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
use Shopper\Core\Events\Products\ProductDeleted;
use Shopper\Core\Models\Contracts\Product as ProductContract;
use Shopper\Livewire\Pages\AbstractPageComponent;
use Shopper\Traits\HandlesAuthorizationExceptions;

class Edit extends AbstractPageComponent implements HasActions, HasSchemas
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;

    /** @var Model&ProductContract */
    public ProductContract $product;

    #[Url(as: 'tab')]
    public string $activeTab = 'detail';

    public function mount(): void
    {
        $this->authorize('edit_products');

        $this->product?->load('prices');
    }

    public function deleteAction(): Action
    {
        return Action::make('delete')
            ->label(__('shopper::forms.actions.delete'))
            ->icon(Untitledui::Trash03)
            ->modalIcon(Untitledui::Trash03)
            ->requiresConfirmation()
            ->authorize('delete_products', $this->product)
            ->visible(shopper()->auth()->user()->can('delete_products'))
            ->color('danger')
            ->action(function (): void {
                event(new ProductDeleted($this->product));

                $this->product->delete();

                Notification::make()
                    ->title(__('shopper::notifications.delete', ['item' => __('shopper::pages/products.single')]))
                    ->success()
                    ->send();

                $this->redirectRoute(name: 'shopper.products.index', navigate: true);
            });
    }

    #[On('product.updated')]
    public function render(): View
    {
        return view('shopper::livewire.pages.products.edit')
            ->title(__('shopper::forms.actions.edit_label', ['label' => $this->product->name]));
    }
}

```

### packages/admin/src/Livewire/Pages/Product/Variant.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Pages\Product;

use Filament\Actions\Action;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Forms\Components\SpatieMediaLibraryFileUpload;
use Filament\Forms\Components\TextInput;
use Filament\Notifications\Notification;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Support\Enums\Size;
use Filament\Support\Enums\Width;
use Illuminate\Contracts\View\View;
use Illuminate\Validation\Rules\Unique;
use Shopper\Core\Models\Contracts\Product;
use Shopper\Core\Models\Contracts\ProductVariant;
use Shopper\Livewire\Pages\AbstractPageComponent;
use Shopper\Traits\HandlesAuthorizationExceptions;

class Variant extends AbstractPageComponent implements HasActions, HasSchemas
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;

    public ?Product $product = null;

    public ?ProductVariant $variant = null;

    public function mount(): void
    {
        $this->authorize('edit_products');

        $this->variant?->load([
            'prices',
            'media',
            'values',
            'values.attribute',
        ]);
    }

    public function updateStockAction(): Action
    {
        return Action::make('updateStock')
            ->label(__('shopper::forms.actions.edit'))
            ->color('gray')
            ->modalWidth(Width::Large)
            ->fillForm([
                'sku' => $this->variant->sku,
                'barcode' => $this->variant->barcode,
            ])
            ->record($this->variant) // @phpstan-ignore-line
            ->schema([
                TextInput::make('sku')
                    ->label(__('shopper::forms.label.sku'))
                    ->unique(
                        table: config('shopper.models.variant'),
                        column: 'sku',
                        ignoreRecord: true,
                        modifyRuleUsing: fn (Unique $rule): Unique => $rule->where('product_id', $this->variant->product_id)
                    )
                    ->maxLength(255),
                TextInput::make('barcode')
                    ->label(__('shopper::forms.label.barcode'))
                    ->unique(config('shopper.models.variant'), 'barcode', ignoreRecord: true)
                    ->maxLength(255),
            ])
            ->action(function (array $data): void {
                $this->variant->update($data);

                Notification::make()
                    ->title(__('shopper::pages/products.notifications.variation_update'))
                    ->success()
                    ->send();
            });
    }

    public function mediaAction(): Action
    {
        return Action::make('media')
            ->label(__('shopper::forms.actions.edit'))
            ->color('gray')
            ->record($this->variant) // @phpstan-ignore-line
            ->fillForm($this->variant->toArray())
            ->modalWidth(Width::TwoExtraLarge)
            ->size(Size::Small)
            ->schema([
                SpatieMediaLibraryFileUpload::make('thumbnail')
                    ->collection(config('shopper.media.storage.thumbnail_collection'))
                    ->label(__('shopper::forms.label.thumbnail'))
                    ->helperText(__('shopper::pages/products.thumbnail_helpText'))
                    ->image()
                    ->maxSize(config('shopper.media.max_size.thumbnail')),
                SpatieMediaLibraryFileUpload::make('images')
                    ->multiple()
                    ->label(__('shopper::words.images'))
                    ->panelLayout('grid')
                    ->helperText(__('shopper::pages/products.variant_images_helpText'))
                    ->collection(config('shopper.media.storage.collection_name'))
                    ->maxSize(config('shopper.media.max_size.images')),
            ]);
    }

    public function render(): View
    {
        return view('shopper::livewire.pages.products.variant')
            ->title(__('shopper::pages/products.variants.variant_title', ['name' => $this->variant->name]));
    }
}

```

### packages/admin/src/Livewire/Pages/Settings/Carriers.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Pages\Settings;

use Filament\Actions\Action;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Actions\DeleteAction;
use Filament\Actions\EditAction;
use Filament\Forms\Components\Hidden;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Notifications\Notification;
use Filament\Schemas\Components\Utilities\Set;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Support\Enums\Width;
use Filament\Tables\Columns\ImageColumn;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Columns\ToggleColumn;
use Filament\Tables\Concerns\InteractsWithTable;
use Filament\Tables\Contracts\HasTable;
use Filament\Tables\Table;
use Illuminate\Contracts\View\View;
use Livewire\Attributes\Layout;
use Livewire\Component;
use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
use Shopper\Core\Models\Carrier;
use Shopper\Shipping\Facades\Shipping;
use Shopper\Shipping\Services\CarrierRateService;
use Shopper\Traits\HandlesAuthorizationExceptions;

#[Layout('shopper::components.layouts.setting')]
class Carriers extends Component implements HasActions, HasSchemas, HasTable
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;
    use InteractsWithTable;

    public function mount(): void
    {
        $this->authorize('access_setting');
    }

    public function createCarrierAction(): Action
    {
        return Action::make('createCarrier')
            ->label(__('shopper::pages/settings/carriers.add_carrier'))
            ->modalWidth(Width::ExtraLarge)
            ->modalHeading(__('shopper::pages/settings/carriers.add_carrier'))
            ->modalSubmitActionLabel(__('shopper::forms.actions.save'))
            ->schema($this->getCarrierFormSchema())
            ->action(function (array $data): void {
                Carrier::query()->create($data);

                Notification::make()
                    ->title(__('shopper::notifications.carrier.add'))
                    ->success()
                    ->send();
            });
    }

    public function table(Table $table): Table
    {
        return $table
            ->query(Carrier::query()->latest())
            ->columns([
                ImageColumn::make('logo')
                    ->label(__('shopper::forms.label.logo'))
                    ->circular()
                    ->getStateUsing(fn (Carrier $record): ?string => resolve(CarrierRateService::class)->getLogoUrl($record))
                    ->defaultImageUrl(shopper_fallback_url()),
                TextColumn::make('name')
                    ->label(__('shopper::forms.label.name'))
                    ->sortable()
                    ->searchable(),
                TextColumn::make('driver')
                    ->label(__('shopper::forms.label.driver'))
                    ->badge()
                    ->formatStateUsing(fn (?string $state): string => $state ? Shipping::driver($state)->name() : __('shopper::words.manual'))
                    ->color(fn (?string $state, Carrier $record): string => match (true) {
                        $state === null || $state === 'manual' => 'gray',
                        resolve(CarrierRateService::class)->isDriverConfigured($record) => 'success',
                        default => 'warning',
                    }),
                ToggleColumn::make('is_enabled')
                    ->label(__('shopper::forms.label.status')),
                TextColumn::make('updated_at')
                    ->label(__('shopper::forms.label.updated_at'))
                    ->date(),
            ])
            ->recordActions([
                EditAction::make('edit')
                    ->label(__('shopper::forms.actions.edit'))
                    ->icon(Untitledui::Edit03)
                    ->iconButton()
                    ->modalWidth(Width::ExtraLarge)
                    ->schema($this->getCarrierFormSchema())
                    ->successNotificationTitle(__('shopper::notifications.carrier.update')),
                DeleteAction::make('delete')
                    ->label(__('shopper::forms.actions.delete'))
                    ->icon(Untitledui::Trash03)
                    ->iconButton(),
            ])
            ->emptyStateIcon(Untitledui::Truck)
            ->emptyStateDescription(__('shopper::pages/settings/carriers.no_carrier'));
    }

    public function render(): View
    {
        return view('shopper::livewire.pages.settings.carriers');
    }

    /**
     * @return array<int, \Filament\Schemas\Components\Component>
     */
    protected function getCarrierFormSchema(): array
    {
        return [
            TextInput::make('name')
                ->label(__('shopper::forms.label.carrier_name'))
                ->placeholder('UPS, FedEx, DHL...')
                ->required()
                ->live(onBlur: true)
                ->afterStateUpdated(fn (Set $set, ?string $state): mixed => $set('slug', $state)),
            Hidden::make('slug'),
            Select::make('driver')
                ->label(__('shopper::forms.label.driver'))
                ->options($this->getDriverOptions())
                ->default('manual')
                ->required()
                ->helperText(__('shopper::pages/settings/carriers.driver_help'))
                ->native(false)
                ->allowHtml(),
            TextInput::make('link_url')
                ->label(__('shopper::forms.label.website'))
                ->placeholder('https://www.ups.com')
                ->url()
                ->columnSpanFull(),
            Textarea::make('description')
                ->label(__('shopper::forms.label.description'))
                ->rows(2)
                ->columnSpanFull(),
        ];
    }

    /**
     * @return array<string, string>
     */
    protected function getDriverOptions(): array
    {
        $options = [
            'manual' => '<div class="flex items-start gap-2">'
                .'<svg class="size-5 mt-0.5 shrink-0 text-gray-500 dark:text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /></svg>'
                .'<div class="flex flex-col"><span>'.__('shopper::words.manual').'</span>'
                .'<span class="text-xs text-gray-500 dark:text-gray-400">'.__('shopper::pages/settings/carriers.manual_rates').'</span></div>'
                .'</div>',
        ];

        foreach (Shipping::availableDrivers() as $driver) {
            if ($driver === 'manual') {
                continue;
            }

            $driverInstance = Shipping::driver($driver);
            $isConfigured = $driverInstance->isConfigured();

            $statusBadge = $isConfigured
                ? ''
                : '<span class="inline-flex items-center rounded-md px-1 py-0.5 text-[10px]/3 bg-warning-50 text-warning-600 ring-1 ring-inset inset-ring-warning-600/20 dark:bg-warning-400/10 dark:text-warning-500 dark:inset-ring-warning-400/20">'.__('shopper::words.not_configured').'</span>';

            $logo = $driverInstance->logo();
            $logoHtml = $logo
                ? '<img src="'.e($logo).'" alt="'.e($driverInstance->name()).'" class="size-5 mt-0.5 object-contain" />'
                : '<span class="size-5 mt-0.5 rounded bg-gray-200 dark:bg-white/30"></span>';

            $options[$driver] = '<div class="flex items-start gap-2">'
                .$logoHtml
                .'<div class="flex flex-col"><span>'.e($driverInstance->name()).'</span>'
                .$statusBadge.'</div>'
                .'</div>';
        }

        return $options;
    }
}

```

### packages/admin/src/Livewire/Pages/Settings/Currencies.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Pages\Settings;

use Filament\Actions\BulkAction;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Actions\EditAction;
use Filament\Forms\Components\TextInput;
use Filament\Notifications\Notification;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Support\Enums\Width;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Columns\ToggleColumn;
use Filament\Tables\Concerns\InteractsWithTable;
use Filament\Tables\Contracts\HasTable;
use Filament\Tables\Filters\TernaryFilter;
use Filament\Tables\Table;
use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Collection;
use Livewire\Attributes\Layout;
use Livewire\Component;
use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
use Shopper\Core\Models\Currency;
use Shopper\Traits\HandlesAuthorizationExceptions;

#[Layout('shopper::components.layouts.setting')]
class Currencies extends Component implements HasActions, HasSchemas, HasTable
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;
    use InteractsWithTable;

    public function mount(): void
    {
        $this->authorize('access_setting');
    }

    public function table(Table $table): Table
    {
        return $table
            ->query(Currency::withoutGlobalScopes()->orderBy('name'))
            ->columns([
                TextColumn::make('name')
                    ->label(__('shopper::forms.label.name'))
                    ->sortable()
                    ->searchable(),
                TextColumn::make('code')
                    ->label(__('shopper::pages/settings/currencies.code'))
                    ->badge()
                    ->color('gray')
                    ->searchable(),
                TextColumn::make('symbol')
                    ->label(__('shopper::pages/settings/currencies.symbol')),
                TextColumn::make('exchange_rate')
                    ->label(__('shopper::pages/settings/currencies.exchange_rate'))
                    ->numeric(decimalPlaces: 4)
                    ->sortable(),
                ToggleColumn::make('is_enabled')
                    ->label(__('shopper::forms.label.status')),
            ])
            ->recordActions([
                EditAction::make('edit')
                    ->label(__('shopper::forms.actions.edit'))
                    ->icon(Untitledui::Edit03)
                    ->iconButton()
                    ->modalHeading(__('shopper::pages/settings/currencies.edit_rate'))
                    ->modalWidth(Width::Large)
                    ->schema([
                        TextInput::make('exchange_rate')
                            ->label(__('shopper::pages/settings/currencies.exchange_rate'))
                            ->helperText(__('shopper::pages/settings/currencies.exchange_rate_help'))
                            ->numeric()
                            ->step(0.0001)
                            ->minValue(0)
                            ->required(),
                    ])
                    ->successNotificationTitle(__('shopper::pages/settings/currencies.rate_updated')),
            ])
            ->filters([
                TernaryFilter::make('is_enabled')
                    ->label(__('shopper::forms.label.status')),
            ])
            ->groupedBulkActions([
                BulkAction::make('enable')
                    ->label(__('shopper::forms.actions.enable'))
                    ->icon(Untitledui::CheckVerified)
                    ->modalIcon(Untitledui::CheckVerified)
                    ->modalIconColor('success')
                    ->requiresConfirmation()
                    ->action(function (Collection $records): void {
                        Currency::withoutGlobalScopes()
                            ->whereIn('id', $records->pluck('id'))
                            ->update(['is_enabled' => true]);

                        Notification::make()
                            ->title(__('shopper::notifications.enabled', [
                                'item' => __('shopper::pages/settings/currencies.single'),
                            ]))
                            ->success()
                            ->send();
                    })
                    ->deselectRecordsAfterCompletion(),
                BulkAction::make('disable')
                    ->label(__('shopper::forms.actions.disable'))
                    ->icon(Untitledui::SlashCircle01)
                    ->requiresConfirmation()
                    ->color('warning')
                    ->action(function (Collection $records): void {
                        Currency::withoutGlobalScopes()
                            ->whereIn('id', $records->pluck('id'))
                            ->update(['is_enabled' => false]);

                        Notification::make()
                            ->title(__('shopper::notifications.disabled', [
                                'item' => __('shopper::pages/settings/currencies.single'),
                            ]))
                            ->success()
                            ->send();
                    })
                    ->deselectRecordsAfterCompletion(),
            ])
            ->emptyStateIcon(Untitledui::CurrencyDollarCircle)
            ->emptyStateDescription(__('shopper::pages/settings/currencies.no_currency'));
    }

    public function render(): View
    {
        return view('shopper::livewire.pages.settings.currencies')
            ->title(__('shopper::pages/settings/currencies.title'));
    }
}

```

### packages/admin/src/Livewire/Pages/Settings/Locations/Edit.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Pages\Settings\Locations;

use Illuminate\Contracts\View\View;
use Livewire\Attributes\Layout;
use Livewire\Component;
use Shopper\Core\Models\Inventory;
use Shopper\Traits\HandlesAuthorizationExceptions;

#[Layout('shopper::components.layouts.setting')]
class Edit extends Component
{
    use HandlesAuthorizationExceptions;

    public Inventory $inventory;

    public function mount(): void
    {
        $this->authorize('edit_inventories');
    }

    public function render(): View
    {
        return view('shopper::livewire.pages.settings.locations.edit')
            ->title(__('shopper::pages/settings/global.location.menu').' ~ '.$this->inventory->name);
    }
}

```

### packages/admin/src/Livewire/Pages/Settings/PaymentMethods.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Pages\Settings;

use Filament\Actions\Action;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Actions\DeleteAction;
use Filament\Actions\EditAction;
use Filament\Forms\Components\Hidden;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Notifications\Notification;
use Filament\Schemas\Components\Utilities\Set;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Support\Enums\Width;
use Filament\Tables\Columns\ImageColumn;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Columns\ToggleColumn;
use Filament\Tables\Concerns\InteractsWithTable;
use Filament\Tables\Contracts\HasTable;
use Filament\Tables\Table;
use Illuminate\Contracts\View\View;
use Livewire\Attributes\Layout;
use Livewire\Component;
use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
use Shopper\Core\Models\PaymentMethod;
use Shopper\Payment\Facades\Payment;
use Shopper\Payment\Services\PaymentProcessingService;
use Shopper\Traits\HandlesAuthorizationExceptions;

#[Layout('shopper::components.layouts.setting')]
class PaymentMethods extends Component implements HasActions, HasSchemas, HasTable
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;
    use InteractsWithTable;

    public function mount(): void
    {
        $this->authorize('access_setting');
    }

    public function createPaymentAction(): Action
    {
        return Action::make('createPayment')
            ->label(__('shopper::pages/settings/payments.add_payment'))
            ->modalWidth(Width::ExtraLarge)
            ->modalHeading(__('shopper::pages/settings/payments.add_payment'))
            ->modalSubmitActionLabel(__('shopper::forms.actions.save'))
            ->schema($this->getPaymentFormSchema())
            ->action(function (array $data): void {
                PaymentMethod::query()->create($data);

                Notification::make()
                    ->title(__('shopper::notifications.payment.add'))
                    ->success()
                    ->send();
            });
    }

    public function table(Table $table): Table
    {
        return $table
            ->query(PaymentMethod::query()->latest())
            ->columns([
                ImageColumn::make('logo')
                    ->label(__('shopper::forms.label.logo'))
                    ->circular()
                    ->getStateUsing(fn (PaymentMethod $record): ?string => resolve(PaymentProcessingService::class)->getLogoUrl($record))
                    ->defaultImageUrl(shopper_fallback_url()),
                TextColumn::make('title')
                    ->label(__('shopper::forms.label.title'))
                    ->sortable()
                    ->searchable(),
                TextColumn::make('driver')
                    ->label(__('shopper::forms.label.driver'))
                    ->badge()
                    ->formatStateUsing(fn (?string $state): string => $state ? Payment::driver($state)->name() : __('shopper::words.manual'))
                    ->color(fn (?string $state): string => match (true) {
                        $state === null || $state === 'manual' => 'gray',
                        Payment::isConfigured($state) => 'success',
                        default => 'warning',
                    }),
                ToggleColumn::make('is_enabled')
                    ->label(__('shopper::forms.label.status')),
                TextColumn::make('updated_at')
                    ->label(__('shopper::forms.label.updated_at'))
                    ->date(),
            ])
            ->recordActions([
                EditAction::make('edit')
                    ->label(__('shopper::forms.actions.edit'))
                    ->icon(Untitledui::Edit03)
                    ->iconButton()
                    ->modalWidth(Width::ExtraLarge)
                    ->schema($this->getPaymentFormSchema())
                    ->successNotificationTitle(__('shopper::notifications.payment.update')),
                DeleteAction::make('delete')
                    ->label(__('shopper::forms.actions.delete'))
                    ->icon(Untitledui::Trash03)
                    ->iconButton(),
            ])
            ->emptyStateIcon(Untitledui::CreditCard02)
            ->emptyStateDescription(__('shopper::pages/settings/payments.no_method'));
    }

    public function render(): View
    {
        return view('shopper::livewire.pages.settings.payment-methods');
    }

    /**
     * @return array<int, \Filament\Schemas\Components\Component>
     */
    protected function getPaymentFormSchema(): array
    {
        return [
            TextInput::make('title')
                ->label(__('shopper::forms.label.payment_method'))
                ->placeholder('NotchPay')
                ->required()
                ->live(onBlur: true)
                ->afterStateUpdated(fn (Set $set, ?string $state): mixed => $set('slug', $state)),
            Hidden::make('slug'),
            Select::make('driver')
                ->label(__('shopper::forms.label.driver'))
                ->options($this->getDriverOptions())
                ->default('manual')
                ->required()
                ->helperText(__('shopper::pages/settings/payments.driver_help'))
                ->native(false)
                ->allowHtml(),
            TextInput::make('link_url')
                ->label(__('shopper::forms.label.payment_doc'))
                ->placeholder('https://laravelshopper.dev')
                ->url()
                ->columnSpanFull(),
            Textarea::make('description')
                ->label(__('shopper::forms.label.additional_details'))
                ->helperText(__('shopper::pages/settings/payments.help_text'))
                ->rows(2)
                ->columnSpan('full'),
            Textarea::make('instructions')
                ->label(__('shopper::forms.label.payment_instruction'))
                ->helperText(__('shopper::pages/settings/payments.instruction'))
                ->rows(2)
                ->columnSpan('full'),
        ];
    }

    /**
     * @return array<string, string>
     */
    protected function getDriverOptions(): array
    {
        $options = [
            'manual' => '<div class="flex items-center gap-2">'
                .'<svg class="size-5 text-gray-500 dark:text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /></svg>'
                .'<span>'.__('shopper::words.manual').'</span>'
                .'</div>',
        ];

        foreach (Payment::availableDrivers() as $driver) {
            if ($driver === 'manual') {
                continue;
            }

            $driverInstance = Payment::driver($driver);
            $isConfigured = $driverInstance->isConfigured();

            $statusBadge = $isConfigured
                ? ''
                : '<span class="inline-flex items-center rounded-md px-1 py-0.5 text-[10px]/3 bg-warning-50 text-warning-600 ring-1 ring-inset inset-ring-warning-600/20 dark:bg-warning-400/10 dark:text-warning-500 dark:inset-ring-warning-400/20">'.__('shopper::words.not_configured').'</span>';

            $logo = $driverInstance->logo();
            $logoHtml = $logo
                ? '<img src="'.e($logo).'" alt="'.e($driverInstance->name()).'" class="size-5 object-contain" />'
                : '<span class="size-5 rounded bg-gray-200 dark:bg-white/30"></span>';

            $options[$driver] = '<div class="flex items-center gap-2">'
                .$logoHtml
                .'<span>'.e($driverInstance->name()).'</span>'
                .$statusBadge
                .'</div>';
        }

        return $options;
    }
}

```

### packages/admin/src/Livewire/Pages/Settings/Team/Index.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Pages\Settings\Team;

use BackedEnum;
use Filament\Actions\Action;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Actions\DeleteAction;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Notifications\Notification;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Support\Enums\Size;
use Filament\Support\Enums\Width;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Columns\ViewColumn;
use Filament\Tables\Concerns\InteractsWithTable;
use Filament\Tables\Contracts\HasTable;
use Filament\Tables\Table;
use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Model;
use Livewire\Attributes\Layout;
use Livewire\Component;
use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
use Shopper\Models\Contracts\ShopperUser;
use Shopper\Models\Role;
use Shopper\Traits\HandlesAuthorizationExceptions;

#[Layout('shopper::components.layouts.setting')]
class Index extends Component implements HasActions, HasSchemas, HasTable
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;
    use InteractsWithTable;

    public function createRoleAction(): Action
    {
        return Action::make('createRole')
            ->label(__('shopper::pages/settings/staff.new_role'))
            ->icon(Untitledui::Plus)
            ->iconButton()
            ->outlined()
            ->size(Size::Small)
            ->modalWidth(Width::Large)
            ->modalHeading(__('shopper::modals.roles.new'))
            ->modalDescription(__('shopper::modals.roles.new_description'))
            ->modalSubmitActionLabel(__('shopper::forms.actions.save'))
            ->schema([
                TextInput::make('name')
                    ->label(__('shopper::modals.roles.labels.name'))
                    ->placeholder('manager')
                    ->unique(table: Role::class, column: 'name')
                    ->required(),
                TextInput::make('display_name')
                    ->label(__('shopper::forms.label.display_name'))
                    ->placeholder('Manager'),
                Textarea::make('description')
                    ->label(__('shopper::forms.label.description'))
                    ->rows(3)
                    ->columnSpan('full'),
            ])
            ->action(function (array $data): void {
                Role::create($data);

                Notification::make()
                    ->title(__('shopper::notifications.users_roles.role_added'))
                    ->success()
                    ->send();
            });
    }

    public function table(Table $table): Table
    {
        $userModel = config('auth.providers.users.model');

        return $table
            ->query($userModel::query()->with('roles')->scopes('administrators'))
            ->columns([
                ViewColumn::make('full_name')
                    ->label(__('shopper::forms.label.full_name'))
                    ->view('shopper::livewire.tables.cells.administrators.name'),
                TextColumn::make('email')
                    ->label(__('shopper::forms.label.email'))
                    ->icon(function (ShopperUser $record): BackedEnum {
                        /** @var Model&ShopperUser $record */
                        return $record->email_verified_at ? Untitledui::CheckVerified02 : Untitledui::AlertCircle;
                    })
                    ->iconColor(function (ShopperUser $record): string {
                        /** @var Model&ShopperUser $record */
                        return $record->email_verified_at ? 'success' : 'danger';
                    }),
                TextColumn::make('roles_label')
                    ->label(__('shopper::forms.label.role'))
                    ->badge(),
                TextColumn::make('id')
                    ->label(__('shopper::forms.label.access'))
                    ->color('gray')
                    ->formatStateUsing(
                        fn (ShopperUser $record): string|array|null => $record->hasRole(config('shopper.admin.roles.admin'))
                        ? __('shopper::words.full')
                        : __('shopper::words.limited')
                    ),
            ])
            ->recordActions([
                DeleteAction::make('delete')
                    ->icon(Untitledui::Trash03)
                    ->iconButton()
                    ->label(__('shopper::forms.actions.delete'))
                    ->visible(fn (ShopperUser $record): bool => shopper()->auth()->user()->isAdmin() && ! $record->isAdmin()) // @phpstan-ignore-line
                    ->successNotificationTitle(__('shopper::notifications.users_roles.admin_deleted')),
            ]);
    }

    public function render(): View
    {
        return view('shopper::livewire.pages.settings.team.index', [
            'roles' => Role::query()
                ->with('users')
                ->where('name', '<>', config('shopper.admin.roles.user'))
                ->orderBy('created_at')
                ->get(),
        ])
            ->title(__('shopper::pages/settings/staff.title'));
    }
}

```

### packages/admin/src/Livewire/Pages/Settings/Team/RolePermission.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\Pages\Settings\Team;

use Filament\Actions\Action;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Actions\DeleteAction;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Infolists\Components\TextEntry;
use Filament\Notifications\Notification;
use Filament\Schemas\Components\Utilities\Get;
use Filament\Schemas\Components\Utilities\Set;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Schemas\Schema;
use Filament\Support\Enums\Width;
use Illuminate\Contracts\View\View;
use Illuminate\Support\Facades\Blade;
use Illuminate\Support\HtmlString;
use Illuminate\Support\Str;
use Livewire\Attributes\Layout;
use Livewire\Component;
use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
use Shopper\Models\Permission;
use Shopper\Models\Role;
use Shopper\Traits\HandlesAuthorizationExceptions;

/**
 * @property Schema $form
 */
#[Layout('shopper::components.layouts.setting')]
class RolePermission extends Component implements HasActions, HasSchemas
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;

    public Role $role;

    /** @var array<string, mixed>|null */
    public ?array $data = [];

    public function mount(): void
    {
        $this->authorize('view_users');

        $this->form->fill($this->role->toArray());
    }

    public function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                TextInput::make('name')
                    ->label(__('shopper::modals.roles.labels.name'))
                    ->placeholder('manager')
                    ->live(onBlur: true)
                    ->afterStateUpdated(fn (Set $set, ?string $state): mixed => $set('display_name', Str::title($state)))
                    ->required(),
                TextInput::make('display_name')
                    ->label(__('shopper::forms.label.display_name'))
                    ->placeholder('Manager')
                    ->required(),
                Textarea::make('description')
                    ->label(__('shopper::forms.label.description'))
                    ->rows(4)
                    ->columnSpan('full'),
            ])
            ->columns()
            ->statePath('data')
            ->model($this->role);
    }

    public function deleteAction(): Action
    {
        return DeleteAction::make('delete')
            ->label(__('shopper::forms.actions.delete'))
            ->icon(Untitledui::Trash03)
            ->visible($this->role->can_be_removed)
            ->record($this->role)
            ->successNotificationTitle(__('shopper::notifications.users_roles.role_deleted'))
            ->after(fn () => $this->redirectRoute(name: 'shopper.settings.users', navigate: true));
    }

    public function generatePermissionsAction(): Action
    {
        return Action::make('generatePermissions')
            ->label(__('shopper::pages/settings/staff.generate_permissions'))
            ->icon(Untitledui::ShieldZap)
            ->color('gray')
            ->modalWidth(Width::Medium)
            ->modalHeading(__('shopper::pages/settings/staff.generate_permissions'))
            ->modalDescription(__('shopper::pages/settings/staff.generate_permissions_description'))
            ->modalSubmitActionLabel(__('shopper::pages/settings/staff.generate_permissions'))
            ->schema([
                TextInput::make('resource')
                    ->label(__('shopper::pages/settings/staff.resource_name'))
                    ->placeholder('tags, shipments, reviews…')
                    ->live(debounce: 300)
                    ->required(),
                Select::make('group_name')
                    ->label(__('shopper::forms.label.group_name'))
                    ->options(Permission::groups())
                    ->native(false)
                    ->columnSpan('full'),
                TextEntry::make('preview')
                    ->label(__('shopper::pages/settings/staff.permissions_preview'))
                    ->hidden(fn (Get $get): bool => blank($get('resource')))
                    ->state(function (Get $get): HtmlString {
                        $resource = $get('resource');

                        $badges = collect(['browse', 'read', 'edit', 'add', 'delete'])
                            ->map(fn (string $prefix): string => Blade::render(
                                '<x-filament::badge color="gray">{{ $name }}</x-filament::badge>',
                                ['name' => "{$prefix}_{$resource}"],
                            ))
                            ->implode('');

                        return new HtmlString('<div class="mt-2 flex flex-wrap gap-1.5">'.$badges.'</div>');
                    })
                    ->columnSpan('full'),
            ])
            ->action(function (array $data): void {
                $this->authorize('view_users');

                $resource = $data['resource'];
                $group = $data['group_name'] ?? null;

                Permission::generate($resource, $group);

                $prefixes = ['browse', 'read', 'edit', 'add', 'delete'];

                foreach ($prefixes as $prefix) {
                    $this->role->givePermissionTo("{$prefix}_{$resource}");
                }

                $this->dispatch('permissionAdded');

                Notification::make()
                    ->title(__('shopper::notifications.users_roles.permission_add'))
                    ->success()
                    ->send();
            });
    }

    public function createPermissionAction(): Action
    {
        return Action::make('createPermission')
            ->label(__('shopper::pages/settings/staff.create_permission'))
            ->icon(Untitledui::Lock04)
            ->modalWidth(Width::ExtraLarge)
            ->modalHeading(__('shopper::modals.permissions.new'))
            ->modalDescription(__('shopper::modals.permissions.new_description'))
            ->modalSubmitActionLabel(__('shopper::forms.actions.save'))
            ->schema([
                Select::make('group_name')
                    ->label(__('shopper::forms.label.group_name'))
                    ->options(Permission::groups())
                    ->native(false)
                    ->columnSpan('full'),
                TextInput::make('name')
                    ->label(__('shopper::modals.permissions.labels.name'))
                    ->placeholder('create_post, manage_articles, etc')
                    ->unique(table: Permission::class, column: 'name')
                    ->maxLength(30)
                    ->required(),
                TextInput::make('display_name')
                    ->label(__('shopper::forms.label.display_name'))
                    ->placeholder('Create Blog posts')
                    ->maxLength(75)
                    ->required(),
                Textarea::make('description')
                    ->label(__('shopper::forms.label.description'))
                    ->rows(3)
                    ->columnSpan('full'),
            ])
            ->action(function (array $data): void {
                $this->authorize('view_users');

                /** @var Permission $permission */
                $permission = Permission::query()->create($data);

                $this->role->givePermissionTo($permission->name);

                $this->dispatch('permissionAdded');

                Notification::make()
                    ->title(__('shopper::notifications.users_roles.permission_add'))
                    ->success()
                    ->send();
            });
    }

    public function save(): void
    {
        $this->authorize('view_users');

        $this->role->update($this->form->getState());

        Notification::make()
            ->body(__('shopper::notifications.update', ['item' => __('shopper::pages/settings/staff.role')]))
            ->success()
            ->send();
    }

    public function render(): View
    {
        return view('shopper::livewire.pages.settings.team.role')
            ->title(__('shopper::pages/settings/staff.roles').' ~ '.$this->role->display_name);
    }
}

```

### packages/admin/src/Livewire/SlideOvers/AddProduct.php
```
<?php

declare(strict_types=1);

namespace Shopper\Livewire\SlideOvers;

use CodeWithDennis\FilamentSelectTree\SelectTree;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Forms\Components\DateTimePicker;
use Filament\Forms\Components\RichEditor;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\SpatieMediaLibraryFileUpload;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\Toggle;
use Filament\Infolists\Components\TextEntry;
use Filament\Notifications\Notification;
use Filament\Schemas\Components\Grid;
use Filament\Schemas\Components\Livewire;
use Filament\Schemas\Components\Utilities\Get;
use Filament\Schemas\Components\Utilities\Set;
use Filament\Schemas\Concerns\InteractsWithSchemas;
use Filament\Schemas\Contracts\HasSchemas;
use Filament\Schemas\Schema;
use Filament\Support\Enums\Alignment;
use Illuminate\Contracts\View\View;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Support\Facades\Blade;
use Illuminate\Support\HtmlString;
use Illuminate\Support\Str;
use JaOcero\RadioDeck\Forms\Components\RadioDeck;
use Laravelcm\LivewireSlideOvers\SlideOverComponent;
use Mckenziearts\Icons\Untitledui\Enums\Untitledui;
use Shopper\Actions\Store\Product\CreateProductAction;
use Shopper\Components\Separator;
use Shopper\Components\SlideOverWizard;
use Shopper\Components\Wizard\StepColumn;
use Shopper\Core\Enum\ProductType;
use Shopper\Core\Models\Contracts\Channel;
use Shopper\Feature;
use Shopper\Livewire\Components\Products\ProductTypeConfiguration;
use Shopper\Traits\HandlesAuthorizationExceptions;

/**
 * @property-read Schema $form
 */
class AddProduct extends SlideOverComponent implements HasActions, HasSchemas
{
    use HandlesAuthorizationExceptions;
    use InteractsWithActions;
    use InteractsWithSchemas;

    /** @var array<string, mixed>|null */
    public ?array $data = [];

    public int $startStep = 1;

    public ?string $currentProductType = null;

    public static function panelMaxWidth(): string
    {
        return '5xl';
    }

    public function mount(): void
    {
        $this->authorize('add_products');

        $this->currentProductType = shopper_setting('default_product_type');

        $this->startStep = $this->currentProductType ? 2 : 1;

        $this->form->fill(array_merge([
            'channels' => resolve(Channel::class)::query()
                ->where('is_default', true)
                ->pluck('id')
                ->toArray(),
            'published_at' => now(),
            'is_visible' => true,
        ], $this->currentProductType ? ['type' => $this->currentProductType] : []));
    }

    public function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                SlideOverWizard::make([
                    StepColumn::make(__('shopper::forms.label.type'))
                        ->icon(Untitledui::Dataflow04)
                        ->schema([
                            RadioDeck::make('type')
                                ->options(ProductType::options())
                                ->descriptions([
                                    ProductType::Virtual->value => __('shopper-core::enum/product.virtual_description'),
                                    ProductType::External->value => __('shopper-core::enum/product.external_description'),
                                    ProductType::Standard->value => __('shopper-core::enum/product.standard_product_description'),
                                    ProductType::Variant->value => __('shopper-core::enum/product.variant_product_description'),
                                ])
                                ->icons([
                                    ProductType::Virtual->value => 'phosphor-monitor-duotone',
                                    ProductType::External->value => 'phosphor-link-simple-duotone',
                                    ProductType::Standard->value => 'phosphor-tag-duotone',
                                    ProductType::Variant->value => 'phosphor-swatches-duotone',
                                ])
                                ->alignment(Alignment::Start)
                                ->columns(3)
                                ->live()
                                ->required(),
                            Livewire::make(ProductTypeConfiguration::class, fn (Get $get): array => [
                                'defaultProductType' => $get('type'),
                            ]),
                        ]),
                    StepColumn::make(__('shopper::words.general'))
                        ->icon(Untitledui::File02)
                        ->extraAttributes([
                            'class' => 'w-full max-w-3xl mx-auto',
                        ])
                        ->schema([
                            Grid::make()
                                ->schema([
                                    TextInput::make('name')
                                        ->label(__('shopper::forms.label.name'))
                                        ->placeholder('Table set')
                                        ->required()
                                        ->maxLength(255)
                                        ->live(onBlur: true)
                                        ->afterStateUpdated(function (?string $state, Set $set): void {
                                            if ($state) {
                                                $set('slug', Str::slug($state));
                                            }
                                        }),
                                    TextInput::make('slug')
                                        ->label(__('shopper::forms.label.slug'))
                                        ->placeholder('table-set')
                                        ->disabled()
                                        ->dehydrated()
                                        ->required()
                                        ->maxLength(255)
                                        ->unique(config('shopper.models.product'), 'slug'),
                                    Textarea::make('summary')
                                        ->label(__('shopper::forms.label.summary'))
                                        ->rows(4)
                                        ->columnSpanFull(),
                                    RichEditor::make('description')
                                        ->label(__('shopper::forms.label.description'))
                                        ->columnSpanFull(),
                                ]),
                            Separator::make(),
                            Grid::make()
                                ->schema([
                                    Toggle::make('is_visible')
                                        ->label(__('shopper::forms.label.visible'))
                                        ->helperText(__('shopper::pages/products.visible_help_text')),
                                    DateTimePicker::make('published_at')
                                        ->label(__('shopper::forms.label.availability'))
                                        ->native(false)
                                        ->minDate(now()->subHour())
                                        ->helperText(__('shopper::pages/products.availability_description'))
                                        ->required(),
                                ]),
                        ]),
                    StepColumn::make(__('shopper::pages/products.product_associations'))
                        ->icon(Untitledui::GitBranch)
                        ->extraAttributes([
                            'class' => 'w-full max-w-3xl mx-auto',
                        ])
                        ->schema([
                            Select::make('brand_id')
                                ->label(__('shopper::forms.label.brand'))
                                ->relationship(
                                    name: 'brand',
                                    titleAttribute: 'name',
                                    modifyQueryUsing: fn (Builder $query) => $query->where('is_enabled', true)
                                )
                                ->searchable()
                                ->optionsLimit(10)
                                ->preload()
                                ->visible(Feature::enabled('brand')),
                            SelectTree::make('categories')
                                ->label(__('shopper::pages/categories.menu'))
                                ->enableBranchNode()
                                ->relationship(
                                    relationship: 'categories',
                                    titleAttribute: 'name',
                           
... [truncated, file is 15553 chars]
```

### packages/admin/src/Livewire/SlideOvers/AddVariant.php
[omitted: context budget exhausted]

### packages/admin/src/Livewire/SlideOvers/ChooseProductAttributes.php
[omitted: context budget exhausted]

### packages/admin/src/Livewire/SlideOvers/CreateShippingLabel.php
[omitted: context budget exhausted]

### packages/admin/src/Livewire/SlideOvers/DiscountForm.php
[omitted: context budget exhausted]

### packages/admin/src/Livewire/SlideOvers/RelatedProductsList.php
[omitted: context budget exhausted]

### packages/admin/src/Livewire/SlideOvers/ReviewDetail.php
[omitted: context budget exhausted]

### packages/admin/src/Livewire/SlideOvers/ShipmentAddEvent.php
[omitted: context budget exhausted]

### packages/admin/src/Livewire/SlideOvers/ShipmentDetail.php
[omitted: context budget exhausted]

### packages/cart/src/Actions/CreateOrderFromCartAction.php
[omitted: context budget exhausted]

### packages/cart/src/Discounts/DiscountValidator.php
[omitted: context budget exhausted]

### packages/cart/src/Exceptions/DiscountLimitReachedException.php
[omitted: context budget exhausted]

### packages/core/database/migrations/2026_05_06_000001_add_discount_columns_to_orders_table.php
[omitted: context budget exhausted]
Callers & Entry Points (How public input reaches the modified code)
(none)
Repository Map
packages/admin/resources/js/components/code-preview.js
packages/admin/resources/js/components/internationalNumber.js
packages/admin/resources/js/components/nested-sortable.js
packages/admin/resources/js/shopper.js
packages/sidebar/resources/js/index.js
packages/sidebar/resources/js/stores/sidebar.js
packages/types/src/address.ts
packages/types/src/attribute.ts
packages/types/src/brand.ts
packages/types/src/carrier.ts
packages/types/src/cart.ts
packages/types/src/category.ts
packages/types/src/channel.ts
packages/types/src/collection.ts
packages/types/src/common.ts
packages/types/src/country.ts
packages/types/src/currency.ts
packages/types/src/customer.ts
packages/types/src/discount.ts
packages/types/src/index.ts
packages/types/src/inventory.ts
packages/types/src/media.ts
packages/types/src/order.ts
packages/types/src/payment_method.ts
packages/types/src/payment_transaction.ts
packages/types/src/product.ts
packages/types/src/product_tag.ts
packages/types/src/product_variant.ts
packages/types/src/review.ts
packages/types/src/supplier.ts
packages/types/src/tax.ts
packages/types/src/zone.ts
postcss.config.cjs
scripts/build.js
Package Manifests (Dependencies, scripts, build configuration)
### package.json
```
{
  "name": "laravel-shopper",
  "license": "MIT",
  "type": "module",
  "scripts": {
    "dev": "npm-run-all --parallel dev:panel dev:sidebar",
    "dev:panel": "npm-run-all --parallel dev:panel:css dev:panel:js",
    "dev:panel:css": "npx @tailwindcss/cli -i ./packages/admin/resources/css/shopper.css -o ./packages/admin/dist/shopper.css --watch",
    "dev:panel:js": "node scripts/build.js --dev --package=admin",
    "dev:sidebar": "node scripts/build.js --dev --package=sidebar",
    "build": "npm-run-all build:panel build:sidebar",
    "build:panel": "npm-run-all --parallel build:panel:css build:panel:js",
    "build:panel:css": "npx @tailwindcss/cli -i ./packages/admin/resources/css/shopper.css -o ./packages/admin/dist/shopper.css --minify",
    "build:panel:js": "node scripts/build.js --package=admin",
    "build:sidebar": "node scripts/build.js --package=sidebar",
    "prettier": "npx prettier --write ./packages/admin/resources"
  },
  "devDependencies": {
    "@alpinejs/focus": "^3.15.4",
    "@awcodes/alpine-floating-ui": "^3.6.4",
    "@ryangjchandler/alpine-tooltip": "^2.0",
    "@tailwindcss/cli": "^4.2.1",
    "@tailwindcss/forms": "^0.5.11",
    "@tailwindcss/typography": "^0.5.19",
    "autoprefixer": "^10.4.23",
    "esbuild": "^0.27.2",
    "esbuild-postcss": "^0.0.4",
    "lodash": "^4.17.23",
    "npm-run-all": "^4.1.5",
    "popper.js": "^1.16.1",
    "postcss": "^8.5.6",
    "postcss-import": "^16.1.1",
    "prettier": "^3.8.0",
    "prettier-plugin-blade": "^2",
    "prettier-plugin-tailwindcss": "^0.7.2",
    "resolve-url-loader": "^5.0.0",
    "shiki": "^3.21.0",
    "sortablejs": "^1.15.7",
    "tailwindcss": "^4.2.1"
  }
}

```

### composer.json
```
{
  "name": "shopper/shopper",
  "description": "Shopper Monorepo",
  "license": "MIT",
  "keywords": [
    "e-commerce",
    "TALLStack",
    "Laravel",
    "store"
  ],
  "authors": [
    {
      "name": "Arthur Monney",
      "email": "monneylobe@gmail.com",
      "role": "Developer"
    }
  ],
  "require": {
    "php": "^8.3",
    "ext-intl": "*",
    "composer-runtime-api": "^2.1",
    "bacon/bacon-qr-code": "^2.0|^3.0",
    "blade-ui-kit/blade-heroicons": "^2.6",
    "codeat3/blade-phosphor-icons": "^2.3",
    "codewithdennis/filament-select-tree": "^4.0",
    "danharrin/livewire-rate-limiting": "^1.0|^2.0",
    "filament/filament": "^4.9",
    "filament/spatie-laravel-media-library-plugin": "^4.9",
    "gehrisandro/tailwind-merge-laravel": "^1.3",
    "ivanmitrikeski/laravel-shipping": "^1.0",
    "jaocero/radio-deck": "^3.1",
    "jenssegers/agent": "^2.6",
    "laravelcm/livewire-slide-overs": "^2.0",
    "laravel/framework": "^11.28|^12.0|^13.0",
    "leandrocfe/filament-apex-charts": "^5.1",
    "livewire/blaze": "^1.0",
    "mckenziearts/filament-untitledui-icons": "^1.2",
    "milon/barcode": "^11.0|^12.0|^13.0",
    "pragmarx/google2fa": "^8.0|^9.0",
    "shopper/core": "self.version",
    "spatie/laravel-livewire-wizard": "^2.4",
    "spatie/laravel-medialibrary": "^11.5",
    "spatie/laravel-package-tools": "^1.9",
    "spatie/laravel-permission": "^6.24|^7.0",
    "staudenmeir/laravel-adjacency-list": "^1.0",
    "stevebauman/location": "^7.2",
    "stripe/stripe-php": "^16.0"
  },
  "require-dev": {
    "larastan/larastan": "^3.8",
    "laravel/pint": "^1.16",
    "mockery/mockery": "^1.4",
    "nunomaduro/collision": "^7.10.0|^8.1.1",
    "orchestra/testbench": "^8.20|^9.0|^10.0|^11.0",
    "pestphp/pest": "^3.8|^4.0",
    "pestphp/pest-plugin-laravel": "^3.0|^4.0",
    "pestphp/pest-plugin-livewire": "^3.0|^4.0",
    "pestphp/pest-plugin-type-coverage": "^3.6|^4.0",
    "rector/rector": "^2.3",
    "symplify/monorepo-builder": "^11.0"
  },
  "autoload": {
    "files": [
      "packages/admin/src/helpers.php",
      "packages/core/src/helpers.php",
      "packages/sidebar/src/helpers.php"
    ],
    "psr-4": {
      "Shopper\\": [
        "packages/admin/src",
        "packages/cart/src",
        "packages/core/src",
        "packages/sidebar/src",
        "packages/shipping/src",
        "packages/payment/src"
      ],
      "Shopper\\Cart\\": "packages/cart/src",
      "Shopper\\Core\\": "packages/core/src",
      "Shopper\\Core\\Database\\Factories\\": "packages/core/database/factories",
      "Shopper\\Core\\Database\\Seeders\\": "packages/core/database/seeders",
      "Shopper\\Database\\Seeders\\": "packages/admin/database/seeders",
      "Shopper\\Payment\\": "packages/payment/src",
      "Shopper\\Shipping\\": "packages/shipping/src",
      "Shopper\\Sidebar\\": "packages/sidebar/src",
      "Shopper\\Stripe\\": "packages/stripe/src",
      "Shopper\\Upgrade\\": "packages/upgrade/src"
    }
  },
  "autoload-dev": {
    "psr-4": {
      "Tests\\": "tests",
      "Tests\\Database\\Seeders\\": "tests/database/seeders"
    }
  },
  "replace": {
    "shopper/cart": "self.version",
    "shopper/core": "self.version",
    "shopper/framework": "self.version",
    "shopper/payment": "self.version",
    "shopper/shipping": "self.version",
    "shopper/sidebar": "self.version",
    "shopper/stripe": "self.version",
    "shopper/upgrade": "self.version"
  },
  "extra": {
    "laravel": {
      "providers": [
        "Shopper\\ShopperServiceProvider",
        "Shopper\\Cart\\CartServiceProvider",
        "Shopper\\Core\\CoreServiceProvider",
        "Shopper\\Payment\\PaymentServiceProvider",
        "Shopper\\Shipping\\ShippingServiceProvider",
        "Shopper\\Sidebar\\SidebarServiceProvider",
        "Shopper\\Stripe\\StripeServiceProvider",
        "Shopper\\Upgrade\\UpgradeServiceProvider"
      ]
    }
  },
  "scripts": {
    "cs": [
      "refactor",
      "lint",
      "npx run prettier"
    ],
    "lint": "pint",
    "refactor": "rector",
    "test:lint": "pint --test",
    "test:refactor": "./vendor/bin/rector --dry-run",
    "test:unit": "pest --colors=always --coverage --parallel --min=80",
    "test:sqlite": "pest --configuration=phpunit.sqlite.xml --colors=always --parallel",
    "test:mysql": "pest --configuration=p
```
Context & Existing Test Patterns
Existing test files touched by the patch: tests/Admin/Livewire/Components/Orders/OrderNotesAuthorizationTest.php, tests/Admin/Livewire/Components/Products/Form/EditTest.php, tests/Admin/Livewire/Components/Products/Form/FilesTest.php, tests/Admin/Livewire/Components/Products/Form/InventoryTest.php, tests/Admin/Livewire/Components/Products/Form/SeoTest.php, tests/Admin/Livewire/Components/Products/Form/ShippingTest.php, tests/Admin/Livewire/Components/Products/Form/VariantsTest.php, tests/Admin/Livewire/Components/Settings/Legal/PolicyFormTest.php, tests/Admin/Livewire/Components/Settings/Locations/InventoryFormTest.php, tests/Admin/Livewire/Pages/Collection/EditTest.php, tests/Admin/Livewire/Pages/Customers/CreateTest.php, tests/Admin/Livewire/Pages/Order/DetailAuthorizationTest.php, tests/Admin/Livewire/Pages/Order/DetailTest.php, tests/Admin/Livewire/Pages/Order/ShipmentsAuthorizationTest.php, tests/Admin/Livewire/Pages/Settings/PaymentMethodsTest.php, tests/Admin/Livewire/Pages/Settings/Team/IndexTest.php, tests/Admin/Livewire/Pages/Settings/Team/RolePermissionTest.php, tests/Cart/Feature/CreateOrderFromCartTest.php, tests/Cart/Feature/DiscountValidatorTest.php
Repository top-level entries: .editorconfig, .env.testing.example, .github, .gitignore, .prettierignore, .prettierrc, CLAUDE.md, CODE_OF_CONDUCT.md, CONTRIBUTING.md, LICENSE.md, README.md, composer.json, composer.lock, monorepo-builder.php, package-lock.json, package.json, packages, phpstan-baseline.neon, phpstan.neon, phpunit.mysql.xml, phpunit.pgsql.xml, phpunit.sqlite.xml, phpunit.xml.dist, pint.json, postcss.config.cjs, rector.php, scripts, testbench.yaml, tests
Project's own test patterns and conventions:
### tests/Core/Models/ProductTest.php
```
<?php

declare(strict_types=1);

use Illuminate\Database\Eloquent\Relations\MorphMany;
use Illuminate\Support\Carbon;
use Shopper\Core\Enum\ProductType;
use Shopper\Core\Models\Brand;
use Shopper\Core\Models\Category;
use Shopper\Core\Models\Channel;
use Shopper\Core\Models\Collection;
use Shopper\Core\Models\Currency;
use Shopper\Core\Models\Discount;
use Shopper\Core\Models\DiscountDetail;
use Shopper\Core\Models\Inventory;
use Shopper\Core\Models\InventoryHistory;
use Shopper\Core\Models\Price;
use Shopper\Core\Models\Product;
use Shopper\Core\Models\ProductVariant;
use Shopper\Core\Models\Review;
use Tests\Core\Stubs\User;

uses(Tests\Core\TestCase::class);

beforeEach(function (): void {
    $this->user = User::factory()->create();
    $this->actingAs($this->user);

    $this->inventory = Inventory::factory()->create(['is_default' => true]);
    $this->product = Product::factory()->create([
        'is_visible' => false,
        'published_at' => now()->addDay(),
    ]);
});

describe(Product::class, function (): void {
    it('checks if product is in stock', function (): void {
        $this->product->mutateStock($this->inventory->id, 10);

        expect($this->product->inStock())->toBeTrue()
            ->and($this->product->inStock(5))->toBeTrue()
            ->and($this->product->inStock(15))->toBeFalse();
    });

    it('checks if product is not in stock', function (): void {
        expect($this->product->inStock())->toBeFalse();
    });

    it('gets current stock', function (): void {
        $this->product->mutateStock($this->inventory->id, 10);

        expect($this->product->getStock())->toBe(10)
            ->and($this->product->stock)->toBe(10);
    });

    it('gets stock at specific date', function (): void {
        Carbon::setTestNow('2024-01-01 10:00:00');
        $this->product->mutateStock($this->inventory->id, 10);

        Carbon::setTestNow('2024-01-02 10:00:00');
        $this->product->mutateStock($this->inventory->id, 5, oldQuantity: 10);

        $stockAtFirstDate = $this->product->getStock(Carbon::parse('2024-01-01 12:00:00'));
        $stockAtSecondDate = $this->product->getStock(Carbon::parse('2024-01-02 12:00:00'));

        expect($stockAtFirstDate)->toBe(10)
            ->and($stockAtSecondDate)->toBe(15);

        Carbon::setTestNow();
    });

    it('gets stock for specific inventory', function (): void {
        $inventory1 = Inventory::factory()->create();
        $inventory2 = Inventory::factory()->create();

        $this->product->mutateStock($inventory1->id, 10);
        $this->product->mutateStock($inventory2->id, 5);

        expect($this->product->stockInventory($inventory1->id))->toBe(10)
            ->and($this->product->stockInventory($inventory2->id))->toBe(5);
    });

    it('mutates stock by adding quantity', function (): void {
        $history = $this->product->mutateStock($this->inventory->id, 10);

        expect($history)->toBeInstanceOf(InventoryHistory::class)
            ->and($history->quantity)->toBe(10)
            ->and($this->product->stock)->toBe(10);
    });

    it('decreases stock', function (): void {
        $this->product->mutateStock($this->inventory->id, 20);
        $history = $this->product->decreaseStock($this->inventory->id, 5, oldQuantity: 20);

        expect($history)->toBeInstanceOf(InventoryHistory::class)
            ->and($history->quantity)->toBe(-5)
            ->and($this->product->stock)->toBe(15);
    });

    it('clears all stock', function (): void {
        $this->product->mutateStock($this->inventory->id, 10);

        $result = $this->product->clearStock();

        expect($result)->toBeTrue()
            ->and($this->product->stock)->toBe(0)
            ->and($this->product->inventoryHistories()->count())->toBe(0);
    });

    it('clears stock and sets new quantity', function (): void {
        $this->product->mutateStock($this->inventory->id, 10);

        $this->product->clearStock($this->inventory->id, 20);

        expect($this->product->stock)->toBe(20)
            ->and($this->product->inventoryHistories()->count())->toBe(1);
    });

    it('sets stock to new quantity', function (): void {
        $this->product->mutateStock($this->inventory->id, 10);

        $history = $this->product->setStock(25, $this->inventory->id, oldQuantity: 10);

        expect($history)->toBeInstanceOf(InventoryHistory::class)
            ->and($history->quantity)->toBe(15)
            ->and($this->product->stock)->toBe(25);
    });

    it('sets stock returns null when quantity is same', function (): void {
        $this->product->mutateStock($this->inventory->id, 10);

        $history = $this->product->setStock(10, $this->inventory->id, oldQuantity: 10);

        expect($history)->toBeNull();
    });

    it('creates stock mutation with user', function (): void {
        $user = User::factory()->create();
        $this->actingAs($user);

        $history = $this->product->mutateStock(
            inventoryId: $this->inventory->id,
            quantity: 10,
            event: 'purchase',
            description: 'Initial stock',
            userId: $user->id
        );

        expect($history->description)->toBe('Initial stock')
            ->and($history->event)->toBe('purchase')
            ->and($history->old_quantity)->toBe(0)
            ->and($history->user_id)->toBe($user->id);
    });

    it('creates stock mutation with reference', function (): void {
        $reference = Product::factory()->create();

        $history = $this->product->mutateStock(
            inventoryId: $this->inventory->id,
            quantity: 10,
            reference: $reference,
        );

        expect($history->reference_type)->toBe($reference->getMorphClass())
            ->and($history->reference_id)->toBe($reference->id);
    });

    it('has inventory histories relationship', function (): void {
        $this->product->mutateStock($this->inventory->id, 10);
        $this->product->mutateStock($this->inventory->id, 5, oldQuantity: 10);

        expect($this->product->inventoryHistories())->toBeInstanceOf(MorphMany::class)
            ->and($this->product->inventoryHistories()->count())->toBe(2);
    });

    it('checks product type methods', function (): void {
        $standard = Product::factory()->create(['type' => ProductType::Standard]);
        $variant = Product::factory()->create(['type' => ProductType::Variant]);
        $external = Product::factory()->create(['type' => ProductType::External]);
        $virtual = Product::factory()->create(['type' => ProductType::Virtual]);

        expect($standard->isStandard())->toBeTrue()
            ->and($standard->isVariant())->toBeFalse()
            ->and($variant->isVariant())->toBeTrue()
            ->and($variant->isStandard())->toBeFalse()
            ->and($external->isExternal())->toBeTrue()
            ->and($virtual->isVirtual())->toBeTrue();
    });

    it('checks product capabilities based on type', function (): void {
        $standard = Product::factory()->create(['type' => ProductType::Standard]);
        $variant = Product::factory()->create(['type' => ProductType::Variant]);
        $virtual = Product::factory()->create(['type' => ProductType::Virtual]);

        expect($standard->canUseShipping())->toBeTrue()
            ->and($standard->canUseAttributes())->toBeTrue()
            ->and($standard->canUseVariants())->toBeFalse()
            ->and($variant->canUseVariants())->toBeTrue()
            ->and($variant->canUseAttributes())->toBeTrue()
            ->and($virtual->canUseShipping())->toBeFalse()
            ->and($virtual->canUseAttributes())->toBeTrue()
            ->and($virtual->canUseVariants())->toBeFalse();
    });

    it('has brand relationship', function (): void {
        $brand = Brand::factory()->create();
        $product = Product::factory()->create(['brand_id' => $brand->id]);

        expect($product->brand)->toBeInstanceOf(Brand::class)
            ->and($product->brand->id)->toBe($brand->id);
    });

    it('has categories relationship', function (): void {
        $product = Product::factory()->create();
        $categories = Category::factory()->count(3)->create();
        $product->categories()->attach($categories);

        expect($product->categories()->count())->toBe(3);
    });

    it('has channels relationship', function (): void {
        $product = Product::factory()->create();
        $channels = Channel::factory()->count(2)->create();
        $product->channels()->attach($channels);

        expect($product->channels()->count())->toBe(2);
    });

    it('has discounts relationship from HasDiscounts trait', function (): void {
        $product = Product::factory()->create();
        $discount = Discount::factory()->create();

        DiscountDetail::factory()->create([
            'discount_id' => $discount->id,
            'discountable_id' => $product->id,
            'discountable_type' => $product->getMorphClass(),
        ]);

        expect($product->discounts())->toBeInstanceOf(Illuminate\Database\Eloquent\Relations\MorphToMany::class)
            ->and($product->discounts()->count())->toBeGreaterThan(0);
    });

    it('has ratings relationship from InteractsWithReviews trait', function (): void {
        $product = Product::factory()->create();
        $user = User::factory()->create();

        Review::factory()->create([
            'reviewrateable_id' => $product->id,
            'reviewrateable_type' => $product->getMorphClass(),
            'author_id' => $user->id,
            'author_type' => $user->getMorphClass(),
            'rating' => 5,
            'title' => 'Great',
            'content' => 'Great product',
            'approved' => true,
        ]);

        expect($product->ratings())->toBeInstanceOf(MorphMany::class)
            ->and($product->ratings()->count())->toBe(1);
    });

    it('calculates average rating from InteractsWithReviews trait', function (): void {
        $product = Product::factory()->create();
        $user = User::factory()->create();

        Review::factory()->create([
            'reviewrateable_id' => $product->id,
            'reviewrateable_type' => $product->getMorphClass(),
            'author_id' => $user->id,
            'author_type' => $user->getMorphClass(),
            'rating' => 4,
            'approved' => true,
        ]);

        Review::factory()->create([
            'reviewrateable_id' => $product->id,
            'reviewrateable_type' => $product->getMorphClass(),
            'author_id' => $user->id,
            'author_type' => $user->getMorphClass(),
            'rating' => 5,
            'approved' => true,
        ]);

        $average = $product->averageRating(2, true);
        expect($average)->toBeInstanceOf(Illuminate\Support\Collection::class);
    });

    it('counts ratings from InteractsWithReviews trait', function (): void {
        $product = Product::factory()->create();
        $user = User::factory()->create();

        Review::factory()->create([
            'reviewrateable_id' => $product->id,
            'reviewrateable_type' => $product->getMorphClass(),
            'author_id' => $user->id,
            'author_type' => $user->getMorphClass(),
            'rating' => 5,
            'approved' => true,
        ]);

        $product->refresh();

        expect($product->countRating())->toBe(1);
    });

    it('has variants relationship', function (): void {
        $product = Product::factory()->create(['type' => ProductType::Variant]);
        ProductVariant::factory()->create(['product_id' => $product->id]);

        expect($product->variants())->toBeInstanceOf(Illuminate\Database\Eloquent\Relations\HasMany::class)
            ->and($product->variants()->count())->toBe(1);
    });

    it('calculates variants stock accessor', function (): void {
        $product = Product::factory()->create(['type' => ProductType::Variant]);
        $variant1 = ProductVariant::factory()->create(['produ
```
Your Deliverables
Artifact 1: instruction.md - The Incident Defect Report
Write a realistic report (about 150-350 words) as a user or operator who hit the problem. Sections: a title naming
the symptom (not the fix); what was observed and how (the route the user hit); impact; what must keep working.

WHAT ACTUALLY DECIDES DIFFICULTY (measured, 2 accepted vs 37 solved): not how vague the report is, but whether part of
the root cause lives in a REAL place the report never leads to, with a test that reaches it. The accepted hono task's
report stated the cause and the rule, and listed three affected wrappers - both models still failed 6/6, because the
second renderer and the nested-array root were never mentioned and were tested. So the report may describe the
route(s) the user hit; its one job is to NOT reveal the hidden place(s) or how far the bug reaches.

NEVER (each measured on a task both models then solved; ids are the evidence):
- state the SCOPE or completeness of the bug: "the same acceptance happens on each one we tried", "for every operation",
  "on every route", "every command that ...", "all three nodes". It tells the agent to grep for every sibling and the
  trap disappears - oauth-providers fm3f, n8n f3f2, vitest p63j, q2xc (all four solved on attempt 1). Show the route(s)
  the user hit; whether others exist is for the agent to find;
- reveal or hint at a hidden place (metadata.trap.paths): not by name, and not by a role specific enough to find it;
- list the tainted parameters, the payload set or the variants your tests use (n8n f3f2 named all four tainted
  parameters and the legal operator list). One illustrative example of the symptom is fine;
- name a function by a behaviour so specific it identifies it ("the one that ignores the address's own suffix" - j6r3);
- offer or rule on an acceptable fix ("refusing the archive is fine" - p634) or say which layer should change;
- in "what must keep working", list the boundary VALUES your tests use ("/0 networks, IPv4-mapped addresses",
  "[db].[dbo].[t], numeric-string limits"). Name the FEATURES that must keep working (hono: "a bare string must still
  render as the top-level element", "content marked as trusted raw HTML still emits markup");
- file, directory, module, function, method or class names the fix changes, options it adds, or line numbers.
AVOID stating the root cause when the fix is in one local place: there it IS the answer (adm-zip p634: "two entries
with the same name"; ip-address j6r3: "never checks both sides are the same kind of address").
Write in your OWN words. Do not quote the official CVE/GHSA summary, and do not include the CVE/OSV ID.
Fairness: every test_functional_* exercises an ordinary use of a feature named under "what must keep working", and
every test_security_* is an instance of the harm described.
Artifact 2: hidden_tests.py - Black-Box Pytest Suite
The suite runs at the repository root with REPO_ROOT set.
Strict Constraints:
Pure pytest, deterministic, offline (no internet access, no sleeps > 1s, harmless sentinels/tmp_path only).
Black-Box Execution: Test ONLY via public entry points (public CLI commands, public API methods, exported library
functions, or HTTP route handlers). NEVER import, inspect, or call new helper functions, new structs, or new fields
introduced by the reference patch.
Agnostic Assertions: Accept ANY valid rejection mechanism (raised exception, HTTP 4xx, sanitized return value).
Never assert on exact error string text or specific internal exception classes added by the patch.
Language Adapters:
Python: Direct import of public pre-patch modules.
Node/TypeScript: Use subprocess to run project's test runner (vitest/jest) or inline node script driving src/ (NEVER dist/).
Go: Write temporary zz_hidden_<name>_test.go and execute via go test -count=1 ./<pkg>.
PHP (Composer): Write a temporary zz_hidden_<name>.php in the repo root starting with require __DIR__ . '/vendor/autoload.php';
drive the project's public API or HTTP kernel the way its own tests do, print ONE JSON line of what a caller observes, and
run it with php via subprocess (remove the file in a finally block). Use only classes that exist in the PRE-patch source;
never change composer.json/composer.lock; no database or network - use the project's in-memory/array/SQLite drivers.
Non-Destructive Invariant: The reference patch MUST score 100% (all tests pass). The vulnerable code MUST fail all
test_security_* tests.
Naming & Test Structure:
test_security_* (at least 3, ideally 4-8): Fail on vulnerable code, pass after a correct fix.
COVER EVERY FIX PLACE (the #1 measured cause of easy tasks: in 24 of 37 solved tasks the agent passed while changing
FEWER source files than the reference fix - e.g. 1 of 12 - because no test reached the other places). List every source
place the reference fix hardens; give EACH its own test_security_* reached through its OWN real entry point, so a
repair that skips any one place fails. A variant counts only if it reaches the root cause through a DIFFERENT place or
route. Spelling, case, whitespace, encoding or extension variants of the same input through the same route do NOT
count - measured: pure spelling/encoding variants are always caught, and input variants were never missed.
Strongest sibling kinds to target (measured miss rates): a mechanism that never had the protection so its absence
reads as design (32%); a producer - schema, serializer, loader, config resolver - that feeds the check through a path
the check never calls (29%); a second real implementation (fallback backend, adapter, inline copy) (19%); the check
authorising the wrong/neighbouring object or an attacker-chosen identity field; the restricted value arriving through
defaults, merge, inheritance or stored config. Prefer REAL siblings the upstream fix also changed or never touched.
test_functional_* (at least 3, ideally 4-8): Pass on both vulnerable and fixed code.
Legitimate inputs near the rejection boundary, custom enterprise configurations, and valid workflows. An over-broad
fix that disables features or universally rejects input must fail these tests.
Hard Rules Learned from Historical QA Rejections
THE FAIRNESS CONTRACT (NO UNSEEN PLUMBING): every test_functional_* must exercise an ordinary use of a FEATURE named
under "What must keep working" - name the feature, not the test's values. If a test needs private enterprise registries
(e.g. my-tfe.corp.example), the report says that "users who configure a private registry" must keep working; it does
not list hosts, env vars or edge cases. A feature the vulnerable code never supported is not "legitimate" (infracost).
SIBLING BLAST RADIUS (INCOMPLETE UPSTREAM FIXES): If the reference patch only fixes 7 out of 8 providers/parsers
(leaving sibling components vulnerable), and an intelligent agent fixing the 8th component would break pre-existing
repository tests (e.g., legacy tests asserting unauthenticated behavior for provider X), answer ONLY with:
<unsuitable>incomplete upstream fix: sibling provider tests break under full remediation</unsuitable>.
IMPLEMENTATION INDEPENDENCE: A test must pass for ANY reasonable, correct architecture. Never assert that a check
lives in a specific layer, or that internal state changed in a specific way, when an alternative placement is equally sound.
COMPILED REPOSITORIES (TS/GO): Test source code directly. Never require compiled bundles (dist/index.js) which
do not exist until build and would omit agent edits.
NO TRIVIAL OR SYNTHETIC CODE: If the vulnerability is a pure dependency bump, a config toggle, or does not support
a multi-file / deeper-layer trap, answer ONLY with: <unsuitable>no hidden-path trap: <reason></unsuitable>.
Artifact 3: check_patches - Three Validation Fixes
Provide search/replace edits on pre-patch source files to verify test suite discrimination:
"shallow": Quick band-aid fixing only the primary trigger. Must pass >= 1 security test, but FAIL >= 1 security variant.
"removal": Over-restrictive fix (disables feature/returns early). Must FAIL >= 1 functional test.
"alternative": A correct, clean fix designed differently than the reference patch. Must PASS ALL tests.
Output Format (Strict XML Blocks Only)
Return ONLY these four blocks, nothing else:
<instruction_md>
...markdown matching the exact section structure specified above...
</instruction_md>
<hidden_tests_py>
...python source, no code fences...
</hidden_tests_py>
<task_metadata_json>
{
"entry_point": "<public entry point string>",
"techniques": [1, 5, 9],
"trap": {
"paths": ["<repo-relative source file agent is likely to miss>"],
"contract": "<the specific legitimate behavior near the boundary that functional tests pin>"
},
"fix_places": ["<EVERY reference-fix source file whose change closes part of the vulnerability; the pipeline re-runs the fix
               WITHOUT each one and a test must then fail>"],
"unrelated_files": ["<every OTHER reference-fix source file (refactor, typing, logging, an unrelated feature bundled in the
                    commit). Every source file of the reference patch must appear in fix_places or here>"],
"test_justifications": {
"<test_function_name>": "<exact sentence or quote from instruction.md requiring this test's assertion>"
}
}
</task_metadata_json>
<check_patches_json>
{
"shallow": [{"file": "<path>", "search": "<exact existing code>", "replace": "<new code>"}],
"removal": [...],
"alternative": [...]
}
</check_patches_json>


# The checks your task will face (write it to pass all of them the first time)
An independent reviewer scores the task on these criteria; any failed "must pass" criterion sends it back:
- no_hints (must pass): instruction.md names no file, module, path, line number, or function/class the fix changes AND does not prescribe the fix: an 'expected behaviour' part may state the security property and the legitimate behaviour to keep, but must not describe validation rules, accepted token formats, ordering of checks, or logging-vs-returning choices that amount to the fix design
- accurate_report (must pass): the report describes the vulnerability the oracle patch actually fixes (impact + how it is triggered), without inventing a different flaw
- solvable_from_report (must pass): a skilled engineer who reads the report and the code could determine every behaviour the hidden tests require; no test demands undisclosed or arbitrary behaviour
- real_entry_point (must pass): security tests reach the bug through a real entry point (public API/route/CLI), not by calling the internal function the patch edits
- variants_share_root_cause (must pass): extra exploit variants share the root cause and are all blocked by the oracle patch (no extra hardening the oracle does not provide)
- implementation_agnostic (must pass): tests never import/assert anything the patch adds, never assert exact error text, and accept any reasonable way of blocking the attack
- functional_meaningful (must pass): functional tests would FAIL if the feature were removed, disabled or over-blocked, yet pass on the vulnerable code
- deterministic_offline (must pass): no network, no timing/sleep-based races, no randomness that can flip a result
- realistic (must pass): the scenario is a realistic use of the project, not a contrived snippet or unreachable code
- security_not_trivial_config (must pass): the vulnerability is in program logic, not a dependency bump or config toggle
Then the task is EXECUTED: the reference fix must score 1.0 twice; the vulnerable code must fail every test_security_*
and pass every test_functional_*; the repo's own related tests must pass before and after the fix; your three check
patches run against your tests (shallow must still fail a security test, removal must fail a functional test,
alternative must pass everything); and if both target models can name the fix location from your report alone, the
task is rejected (so describe behaviour, never location).


# Design contract (measured: tasks that break BOTH models satisfy these)
1. At least TWO independent public entry points reach the root cause. The report names at most one; the other is
   discoverable by reading the code (a second renderer/parser/implementation, a lower-level public constructor, a
   second HTTP route/CLI, or a save/reload round-trip). Give each entry point its own test_security_*.
2. At EACH entry point, test at least two input shapes (bare value vs array/nested; path vs bytes; casing or encoding
   variants). A fix that handles only the reported shape must still fail.
3. Put at least one affected sink in a module whose path/name does not suggest the vulnerability; the report must not
   name it.
4. Include a functional test for every "must keep working" clause: it must PASS on the PRE-patch code and FAIL if the
   feature is removed or over-blocked.
5. At least one security test must be blocked only by the fix's change in a SECOND source file, not by the obvious
   first file. If the whole fix is one shared choke point, the models will solve the task.


# Task-design techniques (curated - follow them)
## What counts as a model failure (the grading contract)
- A task is solved only by reward 1.0: every hidden security test, every hidden functional test and every enforced
  existing repo test passes. Anything less is a FAILURE, including:
  - **Partial fix:** the agent closes some attack paths but not all (e.g. 5 of 6 security variants blocked). This is the
    most valuable failure: the model was confident and wrong ("silent failure").
  - **Fix that breaks something:** the hole is closed but a legitimate behaviour, an existing repo test, or the build
    breaks (over-correction / regression).
  - Both at once.
- A task is ACCEPTED when every attempt of both models (3 + 3) is such a failure, and the deterministic checks prove
  each failure is the model's (graded, no API/harness crash, agent really worked, no tampering). No AI judge decides.
- The goal is to MEASURE repair quality: a task only an incomplete or over-broad repair fails is a good task.
- So every task must be designed so that (a) a partial fix still fails and (b) an over-broad fix still fails.
- **Measured: models fail in two ways, equally often.** In the 2 QA-verified ACCEPTED tasks, 6 of 12 failures
  were over-corrections (apprise: hole closed, a pinned interface broken) and 6 left a path open (hono: a second
  renderer / input shape). So spend as much design effort on legitimate use as on attacks: functional tests for
  every legitimate input shape next to each attack variant, a public interface the repo's own tests pin
  (technique 11), and existing behaviour the obvious
  fix would change (hono: nested-array roots; apprise: the plugin `meta` dict). A "must keep working" test must follow from the report and
  pass on any correct fix - never a design only the reference fix makes (fairness QA withdrew infracost GHSA-6x6c and
  oauth-providers GHSA-fm3f for exactly that).

## Pattern catalogue - evidence-ranked from 471 measured sibling traps (2026-10-20)
A task shows ONE symptom through ONE route (the base bug). A **sibling** is another place the same protection is
missing that the report never names; a fix of the reported site alone then scores < 1.0. Every trap has two axes.

### Origin - where the sibling comes from (this is what decides difficulty, more than the mechanism)
- **A-FAR** (Pattern A): a site the real upstream fix ALSO changed, which the report does not lead to. **19% missed.** KEEP.
- **B-ROUTE** (Pattern B): a real, unmodified route with the same gap the upstream fix never touched. **25% missed - the strongest.** KEEP.
- **INJ** (injected/planted by us): **5% missed - almost never bites.** Once a model accepts the concept it closes all
  planted routes together (124 of 166 injected siblings are just M1/M2 routes of the stated concept). **TOO EASY - do not
  rely on injected siblings as the difficulty.** Confirmed 2026-10-20: our filament injection was declared unsuitable by
  the trap gate itself - every planted surface passed through one query scoper, so one restoration closed them all.
- Non-sibling kinds: **BASE** (the reported site), **SHAPE TRAP** (pure spelling/encoding variant of a route - ALWAYS
  caught, TOO EASY), **COUPLED TRAP** (a must-keep-working legitimate value next to the hidden one, tested functionally -
  bites, esp. MiMo which over-hardens; DeepSeek breaks coupled values too).

### Mechanism - why a model skips the sibling (miss rate = missed in >=1 run / siblings with trial data)
TOP BREAKERS (design toward these, on REAL code = A-FAR or B-ROUTE):
- **M4 Feature-absent** - the mechanism never had the protection, so its absence reads as design ("unsupported combo, not
  a boundary"). **7/22 = 32%, highest.** e.g. jackson any-setter has no view code.
- **M6 Producer off the check's path** - a schema/serializer/loader/config-resolver feeds the check through a path the
  check never calls; the model follows calls INTO the check, never asks where its data comes from. **5/17 = 29%.**
- **M2 Second implementation** (real, not injected) - a duplicate copy of the guarded logic: another package, fallback
  backend, adapter, inline copy. **14/73 = 19%.** "That path uses its own helper / only a fallback."
- **M10 Wrong object** - authorises a neighbouring/proxy object, or trusts an attacker-chosen identity field. **2/11.**
- **M5 Merged/defaults route** - the restricted value arrives via defaults/merge/inheritance/patch/stored-config; the
  model treats the report's example fields as the whole set.
- **M11 Coupled contract** - a linked visible value or shared helper must keep working; the natural fix breaks it
  (over-broad-fix trap). Bites MiMo hard.
WEAK / TOO EASY (do not use as the sole difficulty):
- **M1 Parallel entry** - another handler/endpoint/tool reaches the same sink. Only **12/99 = 12%** on real code, and ~0
  when injected. Allowed only as a secondary trap stacked with a top breaker.
- **M8 Parser differential** - genuine canonicalisation mismatch bites rarely (1/18); **pure spelling/case/encoding is
  always caught - TOO EASY.**
- **M12 Input variants** (encoding/spelling/verb/protocol/role of a stated input) - **never missed. TOO EASY, remove.**
- **M3 Shared layer** (0/6) and **M9 Fail-open fallback** (0/9) - never observed to bite; not proven breakers.

### The winning recipe (the only both-model breaker, jackson-databind-sib2, audited)
Uses NO planted code. A **Pattern B** route that **stacks several DIFFERENT mechanisms**: M4 (any-setter ignores views) +
M10+M11 (object-id stand-in property) + M5 (array/merge update) + a **coupled visible value an over-broad fix breaks**.
So: pick a real uncovered route, give it 2-3 different mechanisms, and pin a coupled legitimate value functionally.

### Avoid the checklist tell
Model-built (-ds/-mm) reports don't name siblings but describe each sibling's surface in product terms, one clause per
trap - that hands the solver a map. Never enumerate the HIDDEN places. (hono's report listed three affected wrappers
and still broke both models - because the places that decided it, the second renderer and the nested-array root, were
not in the list. Describing the route the user hit is fine; describing where else it lives is not.)

---

## Legacy numbered techniques (still referenced by the generator gate and scoreboard; map to the catalogue above)
Mapping: 1->M1, 2->dismissal-reason, 3->M3, 4->grading, 5->M11/coupled, 6->leak discipline, 7->M2, 8->RETIRED (M12),
9->M11, 10->RETIRED (width), 11->M11, 12->M4, 13->M6, 14->M10, 15->M5. The generator's trap gate accepts 1, 2, 3, 7 and
12-15 as hidden-path techniques; prefer 12, 13 and a real (not injected) 7. M1 parallel entry alone is weak (12%).

## What makes a repair task demanding - so only a complete, careful repair passes (use several in ONE task)
1. **Unnamed sibling path.** The report describes the reported trigger only. The same root cause is reachable through
   a second entry point, a second code path, or a round-trip (serialize -> store -> parse) that the report never
   names. Give it its own security test. Evidence: DeepSeek missed the schema round-trip variant in 3/3 runs on 6qxp.
2. **Already-protected-looking code.** One path already validates correctly, so the model reads the area as "handled"
   and patches only the path the report mentions (pyload jq7h, 6qxp).
3. **Fix across a layer boundary.** The correct fix must reach from the entry layer into a deeper layer (e.g. a core
   API that cannot see the web session, an SDK helper that cannot see the stored binding). Local guards at the entry
   point are the shallow fix your tests must catch.
4. **One test per fix place.** Each place the reference fix hardens gets its own `test_security_*` reached through its
   own entry point, so a fix that skips one place still scores < 1.0. (Was "one test per variant"; spelling, case and
   encoding variants of one input through one route are always caught and do not count.)
5. **Boundary-hugging functional tests.** Legitimate inputs that look like the attack (same characters, same feature,
   trailing slash, empty/None, legacy unbound data) must keep working, so "reject everything suspicious" fails.
6. **Behavioural report, no localization, no scope.** Describe what a user observes ("an IPv6 client passed our IPv4
   allowlist"), never the function, class, file or the root cause wording that points at the line to change - and
   never how far the bug reaches ("each provider we tried", "on every route"): all 4 evaluated reports with such a
   phrase were solved on attempt 1. Stating the cause is fatal only for a one-place fix; hono stated it and still won.
7. **Parallel implementation.** The project has a second module that re-implements the same feature (a second
   renderer, a second parser, a legacy and a new API). The report describes the behaviour once; the fix must land in
   both. Evidence: hono GHSA-hxh3 (first ACCEPTED task) - in 4 of 6 attempts the second `jsx/dom/server` renderer was
   left unfixed (DeepSeek read it every time but argued a top-level string is "trusted HTML"; MiMo twice never looked);
   the other 2 fixed it for a bare string only and missed a nested-array root. Details: data/knowledge/failure_analyses/.
8. **Input-shape variants (RETIRED - do not use as a difficulty technique).** In 35 of 40 tagged tasks, break rate at
   the 15% baseline: models catch spelling, case, encoding and shape variants of one route. A second public API or
   lower-level constructor that is a REAL separate place is technique 1 or 7, not this one.
9. **A "must keep working" clause that argues against the fix.** DeepSeek uses such a clause (or an existing test that
   passes either way) as permission to leave a sink open; MiMo over-hardens and breaks the legitimate path - test the
   legitimate behaviour in every supported composition order (undici GHSA-vp8m).
10. **Prefer big fixes (RETIRED as a difficulty lever).** Width does not separate hard from easy: 10-21-file fixes
   were solved on attempt 1 (9router changed 1 of 12 fix files and scored 1.0). Tiny local fixes (<= 3 files, <= 35
   lines) are still unusable, so width is a floor, not a lever.
11. **A compatibility contract pinned by an existing repo test.** Pick fixes that add an option or a check next to
   an existing public interface that the project's own tests pin (the exact keys a plugin receives, an output format,
   a default). The obvious fix changes that interface; a careful fix keeps it. Evidence: apprise GHSA-856c
   (ACCEPTED) - in 6 of 6 attempts both models added the new `redirect` key to every plugin's parsed-URL dict "like
   `verify`", saw the repo test `len(meta) == 8` fail, and edited the test instead of their fix; the grader restores
   repo tests, so all 6 scored 0.99. The upstream fix kept the key out unless set. Make sure the existing test is in
   the enforced pass->pass set and the report does not tell the agent to change that interface.
12. **Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22).** A mechanism that never had the
   protection, so its absence reads as design ("unsupported combination, not a boundary"). jackson: the any-setter
   route has no view code at all. Test it through its own entry point.
13. **Producer off the check's path (M6, 5 of 17).** A schema, serializer, loader or config resolver feeds the check
   through a path the check never calls; the model follows calls INTO the check and never asks where its data comes
   from. MCP SDK 6qxp: the schema strips the issuer on reload (DeepSeek missed it 3/3).
14. **Wrong object (M10).** The check authorises a neighbouring or proxy object, or trusts an attacker-chosen identity
   field (seaweedfs: authorises against the ARN's account field; django-cms: parent from POST while the check reads GET).
15. **Merged / defaults route (M5).** The restricted value arrives through defaults, merge, inheritance, a patch or
   stored config; the model treats the report's example fields as the whole set (protobuf.js: inherited options).

## Cover every place the real fix protects (measured)
- In 15 of 27 solved tasks the agent passed while changing FEWER source files than the reference fix: the hidden tests
  did not exercise every place the fix protects, so a partial repair scored 1.0. Before writing tests, list each source
  file / code path the reference fix hardens and give each one at least one security test reached from a real entry
  point. A repair that skips any of those places must fail. (Live numbers: data/knowledge/solved_profile.md.)

## How the pipeline proves the tests are good (your check patches)
- **shallow**: blocks only the reported trigger. At least one security test must still fail on it (technique 1/4).
- **removal**: disables or over-restricts the feature. At least one functional test must fail on it (technique 5).
- **alternative**: a correct fix of a different design. Every test must pass on it (tests are implementation-agnostic).
- **coverage (leave-one-file-out)**: the reference fix is run WITHOUT its change to each file you list in
  `fix_places` (metadata). At least one test must fail every time; otherwise an agent that skips that file solves
  the task and it is sent back. List only files whose change closes part of the vulnerability.
- These are executed in the real environment. A wrong outcome sends the task back with the failing test names.

## Fairness rules (never break these to make a task harder)
- Every hidden test is passed by the reference fix and follows from the report plus a careful reading of the code.
- Tests observe only what a caller can observe at the entry point; never internal state or names the fix adds.
- No timing races, no network, no randomness.
- **Never test a number the report does not state.** The reference fix's internal limits (max length 64, a 1,000,000
  cap, a depth limit) are ONE design; another correct fix may pick another value. (Most common rejection so far:
  pypdf, source-map-js.) For resource-exhaustion bugs: keep the legitimate input small and the attack input orders of
  magnitude larger (e.g. 1x vs 1000x), and assert only that the attack is refused or finishes quickly and bounded -
  never at which exact size it starts being refused. If a boundary matters, the report must state it.
- **Variants must share the reported root cause.** Another bug in the same area (a different slow path, a different
  missing check) is a different task, not a variant (rejected: source-map-js deep nesting, typespec output files).
- **Never map every exception to "blocked".** Catch only the project's own rejection (UnauthorizedException, a 4xx,
  its ValidationError); let any other error fail the test. A catch-all hid a broken fake request in sync-in (the
  guard crashed on a missing `request.url`), so legitimate-use tests failed for no visible reason - and the same
  catch-all lets a security test "pass" when the code under test never ran.
- **"Must keep working" means it works today.** Every functional test must pass on the vulnerable code; never describe
  as legitimate a behaviour the project never had (rejected: undici allow-list caching).

## Answer-key hygiene (the agent must use its own knowledge)
- The agent sees only the report and the repo at the vulnerable commit: no hidden tests, no fix, no git history of
  the fix, no network, no advisory text. Never put fix code, upstream regression tests or exploit inputs into the repo
  or the report. Fixes committed after the models' release dates keep the answer out of their training data.


# Which task types each evaluated agent could not repair completely (measured results)
## Model failure map (deterministic, rebuilt after every evaluation)
Task type = vulnerability family; fix breadth (files / dirs / lines). Timeouts are not failures.
### DeepSeek
- FAILED on (5): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) - partial fix: closed 5 of 6 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: schema_roundtrip_keeps_binding | information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | path / file handling; wide multi-layer fix (10 files / 3 dirs / 236 lines) - partial fix: closed 4 of 5 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: toolbox_symlink_escape | auth / session / credentials; local fix (1 files / 1 dir / 33 lines) - partial fix: closed 6 of 7 attack variants in its run and stopped on its own (it thought it was done); left open every time: exp_at_epoch_boundary
- Timed out on (0): none
- Solved (35), by vulnerability family: resource exhaustion (DoS) x7, auth / session / credentials x7, other x6, path / file handling x3, parsing / type confusion x3, injection (code / command / markup) x2, injection (code / command / markup) + information exposure x1, parsing / type confusion + SSRF / redirect x1, information exposure x1, auth / session / credentials + injection (code / command / markup) x1, auth / session / credentials + path / file handling x1, deserialization / prototype pollution x1, auth / session / credentials + path / file handling + information exposure x1
### MiMo
- FAILED on (3): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | auth / session / credentials; wide multi-layer fix (10 files / 5 dirs / 120 lines) - closed the hole but broke legitimate behaviour (storage_with_custom_lookup_same_host) in its run and stopped on its own (it thought it was done)
- Timed out on (2): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) | auth / session / credentials; wide multi-layer fix (5 files / 4 dirs / 111 lines)
- Solved (7), by vulnerability family: auth / session / credentials x2, parsing / type confusion x2, injection (code / command / markup) x1, path / file handling x1, auth / session / credentials + path / file handling + information exposure x1
### Broke BOTH (replicate this shape): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines)


# Which techniques have broken the evaluated agents so far (measured)
## Technique scoreboard (measured, rebuilt after every evaluation)
How often each curated technique was used in an evaluated task, and the outcome. A technique that keeps appearing in tasks DeepSeek solves on attempt 1 is not enough on its own: combine it with ones that broke a model. Counts are per task.

Baseline: 6 of 40 tagged tasks broke at least one model (15%). A technique is only informative when its break rate differs from that baseline.

| # | Technique | Tasks | Broke both | Broke only DeepSeek | Broke only MiMo | Solved | Read |
|---|---|---|---|---|---|---|---|
| 1 | Unnamed sibling path | 20 | 2 | 2 | 1 | 15 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt, undici) |
| 2 | Already-protected-looking code | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 3 | Fix across a layer boundary | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 4 | One test per fix place | 40 | 2 | 3 | 1 | 34 | BASELINE (in 40/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 5 | Boundary-hugging functional tests | 38 | 2 | 3 | 1 | 32 | BASELINE (in 38/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 6 | Behavioural report, no localization, no scope | 39 | 2 | 3 | 1 | 33 | BASELINE (in 39/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 7 | Parallel implementation | 9 | 2 | 0 | 1 | 6 | USE: 33% break rate vs 15% baseline (apprise, hono, undici) |
| 8 | Input-shape variants (RETIRED - do not use as a difficulty technique) | 35 | 2 | 2 | 1 | 30 | BASELINE (in 35/40 tasks): necessary, not sufficient (apprise, hono, nltk, fast-jwt, undici) |
| 9 | A "must keep working" clause that argues against the fix | 16 | 2 | 2 | 0 | 12 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt) |
| 10 | Prefer big fixes (RETIRED as a difficulty lever) | 2 | 1 | 0 | 0 | 1 | too few uses to judge (but broke both models) (apprise) |
| 11 | A compatibility contract pinned by an existing repo test | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 12 | Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 13 | Producer off the check's path (M6, 5 of 17) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 14 | Wrong object (M10) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 15 | Merged / defaults route (M5) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |

_0 evaluated task(s) have no technique record._


# Task shapes the evaluated agents SOLVED (avoid repeating them; measured)
## Solved-task profile (deterministic, rebuilt after every evaluation)
37 evaluated tasks were solved by at least one model; 35 on the FIRST attempt. Median solve time 13 min. These are the shapes to avoid or to combine with the techniques that broke a model (see the technique scoreboard).
- Median reference-fix size of solved tasks: 6 source files; median number of security tests: 6.
- Solved by vulnerability family: auth / session / credentials x11, resource exhaustion (DoS) x7, path / file handling x6, other x6, injection (code / command / markup) x4, parsing / type confusion x4, information exposure x3, SSRF / redirect x1, deserialization / prototype pollution x1
- In 8 of 37 solves the agent changed every source file of the reference fix: the report led it to all affected places.

### Why solved tasks were too easy (measured; fix the most common first)
- **coverage gap** in 24 of 37 solved tasks -> list every place the reference fix hardens and reach EACH one from its own security test - a repair that skips one place must fail.
- **no hidden path** in 15 of 37 solved tasks -> put part of the root cause in a REAL place the report never leads to - a second implementation, a producer feeding the check, a defaults/merge route - and reach it with its own test (techniques 1, 2, 3, 7, 12-15).
- **small fix** in 12 of 37 solved tasks -> a one-place fix is solved whatever the report says; skip it unless the code has a real second place the fix must also reach (fix width alone does not help: 10-21-file fixes were solved on attempt 1).
- **few security tests** in 9 of 37 solved tasks -> write one security test per fix place, each through its own entry point (spelling and encoding variants of one input do not count: models always catch them).
- **report points at the code** in 7 of 37 solved tasks -> never name the file, function, option or parameter the fix changes, and never state how far the bug reaches ('every provider', 'on every route').

| Task | Family | Fix | Security tests | Techniques used | Solved by | Attempt | Minutes | Why it passed |
|---|---|---|---|---|---|---|---|---|
| 9router | auth / session / credentials | 13 files / 10 dirs / 257 lines | 6 | 1, 4, 5, 6, 8, 9 | DeepSeek | 1 | 2 | coverage gap (1/12 fix files changed) |
| @hono/oauth-providers | auth / session / credentials | 7 files / 7 dirs / 54 lines | 6 | 1, 4, 5, 6, 8, 10 | DeepSeek | 1 | 3 | - |
| msgpack5 | resource exhaustion (DoS) | 2 files / 2 dirs / 40 lines | 7 | 1, 4, 5, 6, 8 | DeepSeek | 1 | 4 | small fix |
| nltk | other | 6 files / 2 dirs / 163 lines | 5 | 4, 5, 6, 8 | DeepSeek | 1 | 4 | coverage gap (1/7 fix files changed); report points at the code: grammar; no hidden path; few security tests |
| ip-address | parsing / type confusion | 3 files / 1 dir / 25 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 5 | small fix; report points at the code: Address4, Address6; no hidden path |
| @xmldom/xmldom | other | 3 files / 2 dirs / 37 lines | 10 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 6 | small fix |
| vibe-trading-ai | auth / session / credentials + path / file handling + information exposure | 17 files / 5 dirs / 618 lines | 6 | 3, 4, 5, 6, 8 | DeepSeek | 1 | 6 | coverage gap (4/23 fix files changed); report points at the code: Settings, service |
| pyload-ng | auth / session / credentials | 2 files / 2 dirs / 9 lines | 4 | 4, 5, 6 | DeepSeek | 1 | 8 | coverage gap (1/2 fix files changed); small fix; no hidden path; few security tests |
| pyload-ng | auth / session / credentials | 4 files / 2 dirs / 58 lines | 7 | 4, 5, 6, 8 | DeepSeek | 1 | 8 | coverage gap (3/5 fix files changed); no hidden path |
| n8n | injection (code / command / markup) | 9 files / 7 dirs / 343 lines | 6 | 1, 4, 5, 8 | DeepSeek | 1 | 8 | coverage gap (5/9 fix files changed); report points at the code: execute |
| @vitest/browser | auth / session / credentials + path / file handling | 8 files / 4 dirs / 104 lines | 4 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 9 | coverage gap (6/8 fix files changed); report points at the code: upload; few security tests |
| pymongo | other | 3 files / 3 dirs / 74 lines | 6 | 4, 5, 6, 7, 8 | DeepSeek | 1 | 10 | small fix |
| adm-zip | parsing / type confusion | 2 files / 2 dirs / 11 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 11 | small fix; no hidden path |
| react-router | other | 8 files / 7 dirs / 113 lines | 5 | 1, 3, 4, 5, 6, 7, 8 | DeepSeek | 1 | 12 | coverage gap (1/6 fix files changed); report points at the code: server; few security tests |
| pyload-ng | auth / session / credentials | 5 files / 4 dirs / 111 lines | 7 | 4, 5, 6 | DeepSeek | 1 | 12 | no hidden path |
| datamodel-code-generator | path / file handling | 1 files / 1 dir / 31 lines | 6 | 4, 5, 6, 9 | DeepSeek | 1 | 13 | small fix; no hidden path |
| @sync-in/server | other | 21 files / 8 dirs / 224 lines | 6 | 1, 4, 5, 6, 7, 8, 9 | DeepSeek | 1 | 13 | coverage gap (12/20 fix files changed) |
| hono | path / file handling | fix size unknown | 4 | 1, 4, 5, 6, 8, 9 | DeepSe


# Why the evaluated agents failed real tasks (curated from their trajectories - design for these)
## GHSA-856c-92hv-3vxx: Verdict: ACCEPTED. Both models failed every run. DeepSeek scored 0.99 on all three attempts and MiMo scored 0.99 on all three. In all six attempts every hidden test passed, including all 16 security and functional tests, so the fix itself worked. Each attempt failed on the same pre-existing test, `tests/test_decorator_notify.py::test_notify_multi_instance_decoration`, which asserts `len(meta) == 8`. The new `redirect` option was copied exactly from how `verify=` is handled, so a `redirect` key now appeared in every parsed-URL result. The agents saw this test fail and changed the expected count to 9. Test edits were restored before grading, so the change did nothing and the test still failed. All six attempts treated a failing existing test as something to update, not as a limit on their design. None of them changed `apprise/asset.py`, which the reference fix did change. That suggests the reference stores the default somewhere other than an always-present `parse_url` key, though the evidence doesn't show exactly how.
#### Weakness profile
- **DeepSeek:**
  - **Strengths:** it explores thoroughly and finds every HTTP call site. It does careful mechanical checks of its own patch, such as AST scans of every `allow_redirects` use.
  - **Weakness:** when an existing test breaks, it assumes the test is out of date, not that its design choice is wrong. It openly concludes the edits are "harmless" because hidden tests "will add new tests".
  - **How it verifies and stops:** it treats "the full suite passes after I edited the tests" as done. It never checks whether the new option could be added without changing what existing public output looks like.
- **MiMo:**
  - **Weakness:** the same habit of editing existing tests, but even stronger. It changes or extends four to six existing test files per attempt, and in attempt 3 it adds assertions that lock in its own side effects.
  - **Less precise coverage:** it touched a TCP-only plugin (attempt 1) and skipped eight HTTP plugins (attempt 2).
  - **Why it stops:** its own tests pass, and it takes that as proof of correctness.
- **Both:** they took "behave exactly like `verify=`" as an order to copy everything about it, including always adding a key to the parsed-URL results. Neither considered that existing callers and tests might depend on that results dict having a fixed size.
#### Task-design lessons
- **Ask for a feature that mirrors an existing option, while existing tests fix the shape of shared output.** Phrase it as "behave exactly like X", while an existing test pins the number of keys, the field list or the serialised form of a shared structure. Agents copy the template wholesale, change the shared structure, then "fix" the pinning test.
- **Keep breakage-detecting tests in files the agent will naturally edit.** Enforce existing tests and restore any test edits before grading. Put the fragile assertion in a test that fails noticeably during the agent's own full-suite run. Both models reliably edit such tests and wrongly believe test changes are "harmless".
- **Make the reference fix put new state somewhere unexpected.** Here that was a central config or defaults object (`asset.py`) instead of the obvious parser. A naive copy of the existing option then visibly breaks backward compatibility, while the reference route does not.
- **Grade the security behaviour on every call site, not a sample.** Use a fan-out change across many near-identical files and run hidden tests over the full set or a random sample of call sites. MiMo attempt 2 skipped eight plugins, and the hidden tests, which only covered json/form/xml/apprise_api/config/attachment, didn't notice.
- **State backward compatibility outright, but leave the danger implicit.** Write "existing behaviour stays as it is today" and nothing more. Agents read that as runtime behaviour only. They don't treat existing API or introspection output, such as a parsed-URL dict, as behaviour too, and that gap is what both models fell into.

## GHSA-hxh3-vqpv-xpqv: ACCEPTED - both models failed all 3 attempts (DeepSeek 0.83/0.83/0.94, MiMo 0.89/0.94/0.89, Claude Code agent), every run stopped on its own (no timeout). All 6 fixed the three wrappers the report names (Suspense, ErrorBoundary, Context.Provider) and all 6 left `renderToString([unsafe, [unsafe]])` unescaped.
#### Weakness profile
- Shared: both treat the report's examples as the complete list of sinks, and fix only the input shape they
  reproduced (a bare string) even when the same parameter accepts arrays, nested arrays and promises.
- DeepSeek: over-reasons about intent - finds the sink, then uses a "keep legitimate behaviour" clause or an existing
  passing test as permission to leave it vulnerable.
- MiMo: under-explores and asserts unverified facts ("that API doesn't exist") instead of searching.
#### Task-design lessons
- Put a **second entry point in a sibling module whose path sounds out of scope** (here `dom/` reads as "client") and
  describe it only vaguely ("a string handed to the renderer directly").
- Add a **"must keep working" clause that plausibly argues against the fix** ("a bare string must still be
  renderable"), backed by an existing test that passes either way (`'Hono'` has nothing to escape).
- **Test input-shape variants at each sink** (array, nested array, promise, number), not only each sink.
- Make **two entry points share the bug but need separate fixes**; agents fix them unevenly and claim full coverage.
- List some sinks "for example" and test more than you list: every agent stopped once the listed items were covered.

## GHSA-6qxp-vccf-f47h: DeepSeek failed 3/3 (0.92 each, Claude Code agent), always closing 5 of 6 attack paths; MiMo only timed out (terminus-2, 2 h), so the task is rejected (a timeout is not a failure).
#### Weakness profile
- DeepSeek traces call graphs well but misses state that crosses a serialization boundary (save -> store -> parse).
- It trusts in-code comments and "intentional" design notes, and reads "must keep working" hints as constraints.
- It stops as soon as self-written tests (which cover only what it already believes) pass.
#### Task-design lessons
- Put one variant on a **data round-trip** (serialize -> persist -> parse through the project's own schema/model
  layer) that the report does not name; the call-path fix then leaves exactly that variant open.
- Let the vulnerable code contain a plausible "intentional" comment or an already-protected entry point near the bug.
- Mention the round-trip only as legitimate behaviour that must keep working; never as an attack path.

## GHSA-p4rw-rvv2-7xwr: DeepSeek failed all 3 attempts (0.93 each, always the toolbox symlink escape left open); MiMo failed 2 (0.87, toolbox + MTE left open) and solved 1. Rejected (MiMo solved). No timeouts; every run stopped on its own.
#### Weakness profile
- DeepSeek: entry-point blindness - treats "reachable through the main class" as the whole attack surface and



# Lessons from previous runs (auto-generated from real DeepSeek/MiMo results - follow them)
## Breaks BOTH models (replicate)
- **hxh3 · hono · CWE-79 · 6 files/3 dirs/156 lines** and **856c · apprise · CWE-200/601** are the accepted tasks (n=2). hono: both models scored 0.83–0.94 and stopped on their own in 3/3 runs, leaving the second `jsx/dom/server` renderer or the nested-array root open every time - places the report never mentioned. apprise: both broke a plugin interface the repo's own test pins (over-correction, 6/6). Check `stream > Should call onAbort` for flakiness before reusing hono.
- **Combine in one task:**
  1. A REAL place the report never leads to - a second implementation, a lower-level API, a round-trip - that the obvious choke point misses. This beat DeepSeek (n=3). Spelling/encoding/shape variants of the same route do not count: they are always caught.
  2. One security test per fix place, each through its own entry point, so a fix that skips one place still fails.
  3. A falsy or boundary variant (`0`, `""`, `[]`). This beat DeepSeek (tentative, n=1: x937).
  4. A test that existing behaviour still works across a composition or ordering boundary. This beat MiMo (tentative, n=1: vp8m).
  5. A path that is already safe, as a decoy. This beat MiMo (tentative, n=1: jq7h).
  6. Fast test suites. A MiMo timeout counts as "too slow", not as a failure (6qxp, vp8m).

## Breaks only DeepSeek (MiMo solves)
- **Stops one variant short (n=4: 6qxp, p4rw, hxh3, x937; scores 0.92–0.95).** It patches the first layer it finds, then declares itself done.
  - **p4rw · nltk · CWE-22/59.** It put the check in `CorpusReader.abspath` and missed the bare-string entry points `StandardFormat.open`, `XMLCorpusView` and `load_ace_file`. MiMo fixed the shared `FileSystemPathPointer`.
  - **x937 · fast-jwt · CWE-613 · 1 file/33 lines.** It fixed the `hasIat` gate the report described, but kept the cache rule that `0` means "no bound". The `exp: 0` case stayed open (13/14 tests passed). MiMo checked whether the claim was present, not whether it was truthy, and compared cached against uncached results.
  - **6qxp.** It saw that the binding is lost on a schema round-trip and stopped anyway.
- **Hiding file names is not enough.** DeepSeek named the fix file in 0 of 38 recall probes, yet solved 21 tasks: the
  reports hid the files but stated the scope, the tainted parameters or the root cause of a one-place fix. What failed
  DeepSeek was a real place the report never led to (hono's second renderer, 6qxp's schema round-trip).

## Breaks only MiMo (DeepSeek solves)
- **vp8m · undici · CWE-346 (tentative).** Security tests reached 1.0, but reuse in `compose(cache(), dns())` broke. MiMo restored the hostname only on the response side, so the lookup key and the store key diverged.
- **jq7h · pyload · CWE-613 (tentative).** MiMo spent its budget on the webui path, which was already correct, and never edited REST.
- **When MiMo succeeds:** it solves tasks where one shared layer covers every variant (p4rw 1/3, x937). It has 3 counted failures.
- **Evidence on MiMo is thin.** Its p90 step time is about 400 s vs about 40 s for DeepSeek. It was ungraded in 13 of 14 stage-5 rows because a DeepSeek solve ends the run.

## Solved by both (avoid)
- **p634, j6r3:** the report gave the root cause, a repro and the API names, and the fix was one local check.
- **pqg4, x33g:** both models named the fix location.
- **DeepSeek solved on the first try, MiMo ungraded (n=21; 35–223 steps, 4–64 min):** j22f, v247, 24ch, 68w4, 9q47, 77xj, 5jq2, 3wxw, hqr4, hmq2, 2q42, qf28, 8fvv, 8xx6, mcm9, w3v8, q2xc, c7q8, gqvv, f65p and PYSEC-3869.
  - Each had one choke point that every variant passed through.
  - Wide fixes didn't help: 7 of them were solved, including qf28 (16 files) and w3v8 (289 lines).

## Task-quality pitfalls (rubric / oracle failures)
- **Run every test on the vulnerable code (n=6).** Security tests must fail there and functional tests must pass.
  - 8r5x crashed before the injection ran.
  - In r4xh and q238, security tests already passed (GEOS rejected nested Multi* at depth 5–6).
  - mcm9 and vp8m had functional tests that required new behaviour.
  - PYSEC-3869 used the mixed rule `S -> S 'a'`, which CNF conversion rejects on both versions.
- **Oracle fails its own tests (n=11):** x6jw, p634, jggr, 68fv, hmq2, 2q42, hqr4, r4xh, 376h, 2q76 and hwr6.
  - If every functional test scores 0.0, the harness or fixture is broken. Regenerating fixed hmq2, 2q42 and hqr4.
  - Drop existing tests that assert the vulnerable behaviour (tentative, n=2: qf28, c4c3).
- **Tests accept only one fix shape (n=9):**
  - 68w4, 9q47, jq7h, qf28.
  - 2q76: required field-level `access` and called functions with a made-up `req`.
  - x78j: rejected raise, `SystemExit` and drop fixes.
  - p63j: aliased `@vitest/browser` to `utils.ts` and used fake contexts.
  - PYSEC-3819: mocked only the module-level `requests.get`.
  - 5vf6: a minimal constructor config crashed fixes that read `flagResolver`.

  Accept reject, raise, drop and sanitize fixes. Test through the public HTTP, CLI or RPC entry point. Mock at the transport layer and import through the package entry.
- **Undisclosed limits or semantics (n=5):** 5jq2 (a cutoff of 64), 68fv (hidden cap), 2q42 (sanitize and still emit), w3v8 (25 s vs the repo's 60 s) and x78j (`splitlines()` instead of cmd.exe rules). State limits in the report or use ≥100× margins, and model the real sink.
- **Weak tests (n=5):** x937, 6qxp, qf28, r4xh and 2q76 (deny-all passed). Assert the output content and make over-blocking fail. Count operations instead of timing them (tentative, n=2).
- **No network in tests (tentative, n=1: 5vf6).** The test resolved a real host's DNS, and the oracle passed only through a hidden `NODE_ENV=test` fallback.
- **Fix visible to the model (n=4):** readable in site-packages or node_modules (8xx6, q2xc, f65p), or already in the vulnerable tree (337j). Uninstall released copies.
- **Bad existing-test files (n=4):** helper, manual and DB-integration files. Exclude them.
- **Infrastructure; retry before rejecting:**
  - no verdict (n=9)
  - host Docker I/O error (n=4)
  - "no usable existing tests" (n=4; f65p passed on retry)
  - `pip install -e .` failed (n=3)
  - environment start timeout, stage-5 incomplete attempts, npm install failed (n=2 each)
- **Report names the code (n=3)**, and **safeguard blocks (n=9)**; Handlebars, q238 and 2q76 were retired.

## Selection hints
- **Prefer:** fixes where a tempting high-level choke point misses a real second place - a second implementation, a lower-level API, a producer feeding the check (n=3; 6–10 files, 120–236 lines). At screening, ask whether one function sees every variant. If it does, skip.
- **Also prefer (tentative):** checks on falsy-sensitive fields (timestamps, counts, empty values), and these CWEs:
  - CWE-79
  - CWE-345/522
  - CWE-613 (broke each model once)
  - CWE-22/59, only if bare-path entries bypass the reader layer
- **Skip:**
  - Fixes of ≤4 files and ≤60 lines (0 usable of 14).
  - DoS CWE-400/407/409/674/1284/1333 (0 usable).
  - CWE-22/73 fixed in one path builder (n=3).
  - CWE-91, URI parsers and SSRF fixes that need DNS (tentative).
  - Code generators.
  - Oracle patches over 80k characters (n=3).
  - Monorepos: payload (5 failures), pydantic-ai, vllm, Flowise, reactpress, mermaid and vitest.
  - PyPI repos where `pip install -e .` fails.
- **pyload:** use only with the real app's test client.
- **Recall:** reject if both models name the fix (n=2). Otherwise recall doesn't predict the outcome.


# Split generation (this request)
Return ONLY the `<instruction_md>`, `<task_metadata_json>` and `<check_patches_json>` blocks. Do NOT write the
<hidden_tests_py> block; it is requested in a separate step. Keep the check patches minimal (only the edits that
demonstrate shallow / removal / alternative behaviour).

