package sonicwall

import (
	"context"
	"fmt"
	"net/url"

	"github.com/gandiva-tech/sonicwall-sdk/go/models"
)

const addressObjectsBase = "/address-objects/ipv4"

// AddressObjectsService provides CRUD operations for SonicOS IPv4 address objects.
type AddressObjectsService struct {
	client *Client
}

// List returns all IPv4 address objects.
func (s *AddressObjectsService) List(ctx context.Context) ([]*models.AddressObjectIPv4, error) {
	var resp models.AddressObjectsListResponse
	if err := s.client.get(ctx, addressObjectsBase, &resp); err != nil {
		return nil, err
	}

	result := make([]*models.AddressObjectIPv4, 0, len(resp.AddressObjects))
	for i := range resp.AddressObjects {
		result = append(result, models.FromWire(resp.AddressObjects[i].AddressObject.IPv4))
	}
	return result, nil
}

// Get returns a specific IPv4 address object by name.
func (s *AddressObjectsService) Get(ctx context.Context, name string) (*models.AddressObjectIPv4, error) {
	path := fmt.Sprintf("%s/name/%s", addressObjectsBase, url.PathEscape(name))
	var env models.AddressObjectEnvelope
	if err := s.client.get(ctx, path, &env); err != nil {
		return nil, err
	}
	return models.FromWire(env.AddressObject.IPv4), nil
}

// Create creates a new IPv4 address object.
// Returns ConflictError if an object with the same name already exists.
func (s *AddressObjectsService) Create(ctx context.Context, obj *models.AddressObjectIPv4) (*models.AddressObjectIPv4, error) {
	envelope := obj.ToEnvelope()
	if err := s.client.post(ctx, addressObjectsBase, envelope, nil); err != nil {
		return nil, err
	}
	return s.Get(ctx, obj.Name)
}

// Update updates an existing IPv4 address object.
// name is the current name of the object (used in the URL path).
func (s *AddressObjectsService) Update(ctx context.Context, name string, obj *models.AddressObjectIPv4) (*models.AddressObjectIPv4, error) {
	path := fmt.Sprintf("%s/name/%s", addressObjectsBase, url.PathEscape(name))
	envelope := obj.ToEnvelope()
	if err := s.client.put(ctx, path, envelope, nil); err != nil {
		return nil, err
	}
	effectiveName := obj.Name
	if effectiveName == "" {
		effectiveName = name
	}
	return s.Get(ctx, effectiveName)
}

// Delete deletes an IPv4 address object by name.
func (s *AddressObjectsService) Delete(ctx context.Context, name string) error {
	path := fmt.Sprintf("%s/name/%s", addressObjectsBase, url.PathEscape(name))
	return s.client.del(ctx, path)
}

// Ensure creates or updates an address object (upsert).
// Returns (object, created, error) where created is true if a new object was created.
func (s *AddressObjectsService) Ensure(ctx context.Context, obj *models.AddressObjectIPv4) (*models.AddressObjectIPv4, bool, error) {
	existing, err := s.Get(ctx, obj.Name)
	if err != nil {
		if IsNotFound(err) {
			created, createErr := s.Create(ctx, obj)
			if createErr != nil {
				return nil, false, createErr
			}
			return created, true, nil
		}
		return nil, false, err
	}

	_ = existing
	updated, err := s.Update(ctx, obj.Name, obj)
	if err != nil {
		return nil, false, err
	}
	return updated, false, nil
}